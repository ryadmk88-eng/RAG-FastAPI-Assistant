import html
import json
import os
import re
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from auth_routes import router as auth_router
from bm25_search import build_bm25
from database import init_db
from semantic_search import MODEL_NAME, load_data
from chat_routes import router as chat_router
from auth import get_logged_in_user

from feedback_routes import router as feedback_router

from chat_service import (
    save_compare_chat,
    save_rag_chat,
)

# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

APP_TITLE = "FastAPI Assistant"
TOP_K = 5
LLM_MODEL = "gpt-6-luna"

BASE_DIR = Path(__file__).resolve().parent
RESULTS_FILE = BASE_DIR / "results" / "final_results_summary.json"
GRAPHS_DIR = BASE_DIR / "results" / "graphs"


# ============================================================
# LOAD RAG COMPONENTS
# ============================================================

print("Loading FastAPI documentation corpus...")
chunks, embeddings = load_data()

print("Loading semantic embedding model...")
embedding_model = SentenceTransformer(MODEL_NAME)

print("Building BM25 index...")
bm25_index = build_bm25(chunks)

print("RAG system ready.")


api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("WARNING: OPENAI_API_KEY was not found in .env")

client = OpenAI(api_key=api_key)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title=APP_TITLE,
    description="RAG-based FastAPI documentation assistant.",
)

SESSION_SECRET = os.getenv("SESSION_SECRET")

if not SESSION_SECRET:
    raise RuntimeError(
        "SESSION_SECRET was not found in .env"
    )

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False,
)

init_db()

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(feedback_router)


# ============================================================
# RETRIEVAL
# ============================================================

def tokenize(text):
    return re.findall(
        r"\b\w+\b",
        text.lower(),
    )


def semantic_search(
    query,
    top_k=TOP_K,
):
    start = time.perf_counter()

    query_embedding = embedding_model.encode(
        query,
        normalize_embeddings=True,
    )

    scores = embeddings @ query_embedding

    ranked_indices = np.argsort(
        scores
    )[::-1][:top_k]

    results = []

    for index in ranked_indices:
        chunk = chunks[index].copy()

        chunk["retrieval_score"] = float(
            scores[index]
        )

        results.append(chunk)

    elapsed_ms = (
        time.perf_counter()
        - start
    ) * 1000

    return results, elapsed_ms


def bm25_search(
    query,
    top_k=TOP_K,
):
    start = time.perf_counter()

    scores = bm25_index.get_scores(
        tokenize(query)
    )

    ranked_indices = np.argsort(
        scores
    )[::-1][:top_k]

    results = []

    for index in ranked_indices:
        chunk = chunks[index].copy()

        chunk["retrieval_score"] = float(
            scores[index]
        )

        results.append(chunk)

    elapsed_ms = (
        time.perf_counter()
        - start
    ) * 1000

    return results, elapsed_ms


# ============================================================
# CONTEXT
# ============================================================

def build_context(
    retrieved_chunks,
):
    source_numbers = {}
    source_data = {}
    context_parts = []

    next_source_number = 1

    for chunk in retrieved_chunks:

        url = str(
            chunk.get(
                "url",
                "",
            )
        )

        if url not in source_numbers:

            source_numbers[url] = (
                next_source_number
            )

            source_data[
                next_source_number
            ] = {
                "number":
                    next_source_number,

                "title":
                    str(
                        chunk.get(
                            "title",
                            "FastAPI Documentation",
                        )
                    ),

                "url":
                    url,

                "score":
                    float(
                        chunk.get(
                            "retrieval_score",
                            0,
                        )
                    ),
            }

            next_source_number += 1

        source_number = source_numbers[url]

        score = float(
            chunk.get(
                "retrieval_score",
                0,
            )
        )

        if score > source_data[
            source_number
        ]["score"]:

            source_data[
                source_number
            ]["score"] = score

        title = str(
            chunk.get(
                "title",
                "",
            )
        )

        heading = str(
            chunk.get(
                "heading",
                "",
            )
        )

        text = str(
            chunk.get(
                "text",
                "",
            )
        )

        context_parts.append(
            (
                f"[Source {source_number}]\n"
                f"Title: {title}\n"
                f"Heading: {heading}\n"
                f"URL: {url}\n"
                f"Content:\n{text}"
            )
        )

    context = "\n\n---\n\n".join(
        context_parts
    )

    return context, source_data


# ============================================================
# AI ANSWER
# ============================================================

def generate_answer(
    question,
    retrieved_chunks,
):
    (
        context,
        source_data,
    ) = build_context(
        retrieved_chunks
    )

    prompt = f"""
You are a technical documentation assistant for FastAPI.

Answer the user's question using ONLY the FastAPI documentation
provided below.

Rules:
1. Use only the supplied FastAPI documentation.
2. Do not invent or assume information.
3. If the supplied documentation is insufficient, clearly say so.
4. Give a useful, clear, and concise technical answer.
5. Include code examples only when supported by the documentation.
6. Cite important factual statements using [Source 1], [Source 2], etc.
7. Only use source numbers that actually appear in the supplied context.
8. Never invent citations or URLs.
9. Do not cite sources that were not provided.
10. Prefer practical explanations suitable for a developer.

User question:
{question}

FastAPI documentation:
{context}
""".strip()

    start = time.perf_counter()

    response = client.responses.create(
        model=LLM_MODEL,
        input=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    generation_ms = (
        time.perf_counter()
        - start
    ) * 1000

    answer = (
        response.output_text
        or ""
    ).strip()

    if not answer:
        answer = (
            "The model did not return an answer."
        )

    return (
        answer,
        source_data,
        generation_ms,
    )


def run_rag(
    question,
    method,
):
    total_start = time.perf_counter()

    if method == "bm25":

        (
            retrieved_chunks,
            retrieval_ms,
        ) = bm25_search(
            question
        )

        label = "BM25 Keyword Search"

    else:

        (
            retrieved_chunks,
            retrieval_ms,
        ) = semantic_search(
            question
        )

        label = "Semantic / Vector Search"

    (
        answer,
        source_data,
        generation_ms,
    ) = generate_answer(
        question,
        retrieved_chunks,
    )

    total_ms = (
        time.perf_counter()
        - total_start
    ) * 1000

    return {
        "method": method,
        "label": label,
        "answer": answer,
        "sources": source_data,
        "retrieval_ms": retrieval_ms,
        "generation_ms": generation_ms,
        "total_ms": total_ms,
    }


# ============================================================
# ANSWER FORMATTING
# ============================================================

def format_text_section(
    text
):
    escaped = html.escape(text)

    escaped = re.sub(
        r"`([^`\n]+)`",
        r"<code>\1</code>",
        escaped,
    )

    escaped = re.sub(
        r"\[Source (\d+)\]",
        (
            r'<span class="citation">'
            r'Source \1'
            r"</span>"
        ),
        escaped,
    )

    lines = escaped.splitlines()

    output = []
    in_list = False

    for line in lines:

        stripped = line.strip()

        if not stripped:

            if in_list:
                output.append("</ul>")
                in_list = False

            continue

        heading = re.match(
            r"^#{1,4}\s+(.+)$",
            stripped,
        )

        if heading:

            if in_list:
                output.append("</ul>")
                in_list = False

            output.append(
                (
                    '<h3 class="answer-subheading">'
                    f"{heading.group(1)}"
                    "</h3>"
                )
            )

            continue

        stripped = re.sub(
            r"\*\*(.+?)\*\*",
            r"<strong>\1</strong>",
            stripped,
        )

        if stripped.startswith(
            ("- ", "* ")
        ):

            if not in_list:
                output.append(
                    '<ul class="answer-list">'
                )

                in_list = True

            output.append(
                f"<li>{stripped[2:]}</li>"
            )

            continue

        numbered = re.match(
            r"^\d+\.\s+(.+)$",
            stripped,
        )

        if numbered:

            if not in_list:
                output.append(
                    '<ul class="answer-list">'
                )

                in_list = True

            output.append(
                f"<li>{numbered.group(1)}</li>"
            )

            continue

        if in_list:
            output.append("</ul>")
            in_list = False

        output.append(
            f"<p>{stripped}</p>"
        )

    if in_list:
        output.append("</ul>")

    return "\n".join(output)


def format_answer(
    answer
):
    parts = re.split(
        (
            r"```(?:[\w+-]+)?"
            r"\s*\n?"
            r"(.*?)```"
        ),
        answer,
        flags=re.DOTALL,
    )

    formatted = []

    for index, part in enumerate(
        parts
    ):

        if not part.strip():
            continue

        if index % 2 == 1:

            code = html.escape(
                part.strip()
            )

            formatted.append(
                f"""
                <div class="code-wrapper">

                    <div class="code-header">

                        <span>
                            Code example
                        </span>

                        <button
                            type="button"
                            onclick="copyCode(this)"
                        >
                            Copy
                        </button>

                    </div>

                    <pre><code>{code}</code></pre>

                </div>
                """
            )

        else:

            formatted.append(
                format_text_section(
                    part
                )
            )

    return "\n".join(
        formatted
    )


def extract_cited_sources(
    answer
):
    citations = re.findall(
        r"\[Source (\d+)\]",
        answer,
    )

    return sorted(
        {
            int(number)
            for number
            in citations
        }
    )


# ============================================================
# SOURCES
# ============================================================

def build_source_cards(
    answer,
    source_data,
    method,
):
    cards = []

    for number in extract_cited_sources(
        answer
    ):

        source = source_data.get(
            number
        )

        if not source:
            continue

        score = float(
            source.get(
                "score",
                0,
            )
        )

        if method == "semantic":
            score_text = (
                f"{score:.3f} similarity"
            )
        else:
            score_text = (
                f"{score:.2f} BM25 score"
            )

        source_url = html.escape(
            str(
                source.get(
                    "url",
                    "",
                )
            ),
            quote=True,
        )

        source_title = html.escape(
            str(
                source.get(
                    "title",
                    "FastAPI Documentation",
                )
            )
        )

        cards.append(
            f"""
            <a
                class="source-card"
                href="{source_url}"
                target="_blank"
                rel="noopener noreferrer"
            >

                <div class="source-top">

                    <span class="source-number">
                        {number}
                    </span>

                    <span class="source-score">
                        {score_text}
                    </span>

                </div>

                <strong>
                    {source_title}
                </strong>

                <small>
                    fastapi.tiangolo.com
                </small>

                <span class="source-link">
                    Open source ↗
                </span>

            </a>
            """
        )

    if not cards:
        return """
        <div class="empty-source">
            No cited sources.
        </div>
        """

    return "\n".join(cards)


# ============================================================
# ERRORS
# ============================================================

def friendly_error(
    exception
):
    message = str(
        exception
    ).lower()

    if (
        "quota" in message
        or "billing" in message
    ):
        return (
            "The AI service currently "
            "has no available API credit."
        )

    if (
        "rate limit" in message
        or "rate_limit" in message
    ):
        return (
            "The AI service is busy. "
            "Please try again."
        )

    if (
        "timeout" in message
        or "timed out" in message
    ):
        return (
            "The request took too long. "
            "Please try again."
        )

    if (
        "api key" in message
        or "authentication" in message
        or "unauthorized" in message
    ):
        return (
            "The AI service could "
            "not authenticate."
        )

    if "connection" in message:
        return (
            "The assistant could not "
            "connect to the AI service."
        )

    return (
        "The assistant could not "
        "complete this request. "
        "Please try again."
    )


# ============================================================
# ANSWER CARD
# ============================================================

def result_card(
    result,
    card_id,
    compact=False,
):
    answer_html = format_answer(
        result["answer"]
    )

    sources_html = build_source_cards(
        result["answer"],
        result["sources"],
        result["method"],
    )

    compact_class = (
        " compact"
        if compact
        else ""
    )

    retrieval_time = (
        f'{result["retrieval_ms"]:.1f} ms'
    )

    generation_time = (
        f'{result["generation_ms"] / 1000:.2f} s'
    )

    total_time = (
        f'{result["total_ms"] / 1000:.2f} s'
    )

    method_label = html.escape(
        str(
            result["label"]
        )
    )

    return f"""
    <article
        class="answer-card{compact_class}"
    >

        <div class="answer-header">

            <div>

                <span class="small-label">
                    Retrieval method
                </span>

                <strong>
                    {method_label}
                </strong>

            </div>


            <div class="answer-actions">

                <button
                    type="button"
                    onclick="
                        copyAnswer(
                            '{card_id}',
                            this
                        )
                    "
                >
                    Copy
                </button>

                <button
                    type="button"
                    onclick="
                        regenerateLastQuestion()
                    "
                >
                    Regenerate
                </button>

            </div>

        </div>


        <div
            class="answer-content"
            id="{card_id}"
        >
            {answer_html}
        </div>


        <div class="performance-row">

            <span>
                Retrieval {retrieval_time}
            </span>

            <span>
                Generation {generation_time}
            </span>

            <span>
                Total {total_time}
            </span>

        </div>


        <div class="sources-block">

            <div class="sources-heading">

                <strong>
                    Sources
                </strong>

                <span>
                    Official FastAPI docs
                </span>

            </div>

            <div class="source-grid">
                {sources_html}
            </div>

        </div>


        <div class="feedback-row">

            <span>
                Was this answer useful?
            </span>

            <button
                type="button"
                class="feedback-button"
                onclick="
                    setHelpful(
                        this,
                        'yes'
                    )
                "
            >
                👍 Yes
            </button>

            <button
                type="button"
                class="feedback-button"
                onclick="
                    setHelpful(
                        this,
                        'no'
                    )
                "
            >
                👎 No
            </button>

            <span class="feedback-thanks">
            </span>

        </div>

    </article>
    """


# ============================================================
# COMPARE MODE
# ============================================================

def compare_summary_card(
    semantic_result,
    bm25_result,
):
    semantic_retrieval = float(
        semantic_result[
            "retrieval_ms"
        ]
    )

    bm25_retrieval = float(
        bm25_result[
            "retrieval_ms"
        ]
    )

    semantic_total = float(
        semantic_result[
            "total_ms"
        ]
    )

    bm25_total = float(
        bm25_result[
            "total_ms"
        ]
    )

    semantic_sources = len(
        extract_cited_sources(
            semantic_result[
                "answer"
            ]
        )
    )

    bm25_sources = len(
        extract_cited_sources(
            bm25_result[
                "answer"
            ]
        )
    )

    if semantic_retrieval < bm25_retrieval:
        retrieval_winner = "Semantic"

    elif bm25_retrieval < semantic_retrieval:
        retrieval_winner = "BM25"

    else:
        retrieval_winner = "Tie"

    if semantic_total < bm25_total:
        total_winner = "Semantic"

    elif bm25_total < semantic_total:
        total_winner = "BM25"

    else:
        total_winner = "Tie"

    return f"""
    <section class="compare-summary">

        <div>
            <span>
                Faster retrieval
            </span>

            <strong>
                {retrieval_winner}
            </strong>
        </div>

        <div>
            <span>
                Faster total response
            </span>

            <strong>
                {total_winner}
            </strong>
        </div>

        <div>
            <span>
                Semantic sources
            </span>

            <strong>
                {semantic_sources}
            </strong>
        </div>

        <div>
            <span>
                BM25 sources
            </span>

            <strong>
                {bm25_sources}
            </strong>
        </div>

    </section>
    """


# ============================================================
# CSS
# ============================================================

CSS = r"""
* {
    box-sizing: border-box;
}

:root {
    --page: #0b0c10;
    --sidebar: #111217;

    --surface: #17181e;
    --surface-2: #1d1f27;
    --surface-3: #242731;

    --text: #f4f4f5;
    --muted: #9b9da6;

    --border:
        rgba(
            255,
            255,
            255,
            0.08
        );

    --accent: #8b72ff;
    --accent-2: #a394ff;

    --accent-soft:
        rgba(
            139,
            114,
            255,
            0.13
        );

    --accent-border:
        rgba(
            139,
            114,
            255,
            0.34
        );

    --danger: #ff7d8d;
}

body[data-theme="light"] {
    --page: #ffffff;
    --sidebar: #f7f7f8;

    --surface: #ffffff;
    --surface-2: #f4f4f5;
    --surface-3: #ececf0;

    --text: #18181b;
    --muted: #686b75;

    --border:
        rgba(
            24,
            24,
            27,
            0.09
        );

    --accent: #6f5bd3;
    --accent-2: #7f6ee0;

    --accent-soft:
        rgba(
            111,
            91,
            211,
            0.09
        );

    --accent-border:
        rgba(
            111,
            91,
            211,
            0.25
        );
}

html,
body {
    margin: 0;
    min-height: 100%;
}

body {
    min-height: 100vh;

    background:
        var(--page);

    color:
        var(--text);

    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}

body.empty-chat {
    overflow: hidden;
}

button,
textarea,
select,
input {
    font: inherit;
    color: inherit;
}

button {
    cursor: pointer;
}

a {
    color: inherit;
    text-decoration: none;
}


/* ============================================================
   LAYOUT
============================================================ */

.app-shell {
    min-height: 100vh;

    display: grid;

    grid-template-columns:
        260px
        minmax(
            0,
            1fr
        );
}

.sidebar {
    position: fixed;

    inset:
        0 auto 0 0;

    z-index: 50;

    width: 260px;
    height: 100vh;

    display: flex;

    flex-direction: column;

    padding: 12px;

    border-right:
        1px solid
        var(--border);

    background:
        var(--sidebar);
}

.main-shell {
    grid-column: 2;

    min-width: 0;

    min-height: 100vh;

    background:
        var(--page);
}

body.empty-chat
.main-shell {
    height: 100vh;
    overflow: hidden;
}


/* ============================================================
   SIDEBAR
============================================================ */

.sidebar-head {
    min-height: 46px;

    display: flex;

    align-items: center;

    justify-content:
        space-between;

    padding:
        0 7px 8px;
}

.sidebar-name {
    font-size: 17px;

    font-weight: 700;

    letter-spacing:
        -0.02em;
}

.sidebar-icon-button {
    width: 34px;
    height: 34px;

    display: grid;

    place-items: center;

    border: 0;

    border-radius: 9px;

    background:
        transparent;

    color:
        var(--muted);

    font-size: 19px;
}

.sidebar-icon-button:hover {
    background:
        var(--surface-2);

    color:
        var(--text);
}

.side-nav {
    display: flex;

    flex-direction: column;

    gap: 4px;
}

.side-action,
.side-link,
.history-item {
    width: 100%;

    min-height: 42px;

    display: flex;

    align-items: center;

    gap: 11px;

    padding:
        0 11px;

    border: 0;

    border-radius: 10px;

    background:
        transparent;

    color:
        var(--text);

    text-align: left;

    font-size: 13px;
}

.side-action:hover,
.side-link:hover,
.history-item:hover,
.side-action.active {
    background:
        var(--surface-2);
}

.side-symbol {
    width: 20px;

    flex:
        0 0 20px;

    color:
        var(--muted);

    text-align: center;
}

.side-section-title {
    padding:
        18px 11px 7px;

    color:
        var(--muted);

    font-size: 11px;

    font-weight: 650;
}

.chat-search {
    display: none;

    padding:
        6px 4px 8px;
}

.chat-search.open {
    display: block;
}

.chat-search input {
    width: 100%;

    padding:
        10px 11px;

    border:
        1px solid
        var(--border);

    border-radius: 10px;

    outline: 0;

    background:
        var(--surface);
}

.chat-search input:focus {
    border-color:
        var(--accent-border);
}

.history-list {
    min-height: 0;

    overflow-y: auto;

    display: flex;

    flex-direction: column;

    gap: 2px;
}

.history-item {
    display: block;

    overflow: hidden;

    text-overflow:
        ellipsis;

    white-space:
        nowrap;
}

.history-empty {
    padding:
        10px 11px;

    color:
        var(--muted);

    font-size: 12px;
}

.sidebar-bottom {
    margin-top: auto;

    padding-top: 9px;

    border-top:
        1px solid
        var(--border);
}

.profile-row {
    display: flex;

    align-items: center;

    gap: 10px;

    padding: 8px;

    border-radius: 10px;
}

.profile-row:hover {
    background:
        var(--surface-2);
}

.profile-avatar {
    width: 30px;
    height: 30px;

    display: grid;

    place-items: center;

    border-radius: 50%;

    background:
        var(--surface-3);

    font-size: 11px;

    font-weight: 700;
}

.profile-copy {
    min-width: 0;

    flex: 1;
}

.profile-copy strong {
    display: block;

    font-size: 12px;
}

.profile-copy span {
    display: block;

    margin-top: 1px;

    color:
        var(--muted);

    font-size: 9px;
}


/* ============================================================
   TOPBAR
============================================================ */

.topbar {
    position: sticky;

    top: 0;

    z-index: 30;

    height: 56px;

    display: flex;

    align-items: center;

    justify-content:
        space-between;

    gap: 16px;

    padding:
        0 18px;

    border-bottom:
        1px solid
        var(--border);

    background:
        var(--page);
}

body.empty-chat
.topbar {
    position: relative;
}

.topbar-left {
    display: flex;

    align-items: center;

    gap: 10px;

    min-width: 0;
}

.topbar-title {
    font-size: 13px;

    font-weight: 650;

    white-space: nowrap;
}

.topbar-right {
    display: flex;

    align-items: center;

    justify-content: flex-end;

    flex-wrap: nowrap;

    gap: 6px;

    white-space: nowrap;
}


/* Search and theme */

.top-button {
    height: 34px;

    padding:
        0 10px;

    display: inline-flex;

    align-items: center;

    justify-content: center;

    border:
        1px solid
        transparent;

    border-radius: 10px;

    background:
        transparent;

    color:
        var(--muted);

    font-size: 11px;

    text-decoration: none;

    white-space: nowrap;
}

.top-button:hover {
    background:
        var(--surface-2);

    color:
        var(--text);
}


/* Sign in pill */

.signin-top {
    padding:
        0 14px;

    border-color:
        var(--accent-border);

    background:
        var(--accent-soft);

    color:
        var(--accent-2);

    font-weight: 650;
}

.signin-top:hover {
    border-color:
        var(--accent);

    background:
        var(--accent);

    color: white;
}


/* Mobile hamburger only */

.mobile-menu {
    display: none;

    width: 34px;
    height: 34px;

    padding: 0;

    place-items: center;

    border: 0;

    border-radius: 9px;

    background:
        transparent;

    color:
        var(--text);

    font-size: 18px;
}

.mobile-menu:hover {
    background:
        var(--surface-2);
}


/* ============================================================
   CHAT AREA
============================================================ */

.chat-area {
    width:
        min(
            820px,
            calc(
                100% - 40px
            )
        );

    margin:
        0 auto;

    padding:
        30px 0 200px;
}


/* No scrolling when empty */

body.empty-chat
.chat-area {
    height:
        calc(
            100vh - 56px
        );

    padding:
        0 0 150px;

    display: grid;

    place-items: center;

    overflow: hidden;
}

.empty-state {
    text-align: center;

    transform:
        translateY(
            -38px
        );
}

.empty-state h1 {
    margin: 0;

    font-size:
        clamp(
            32px,
            4vw,
            45px
        );

    font-weight: 500;

    letter-spacing:
        -0.04em;
}

.empty-state p {
    max-width: 500px;

    margin:
        12px auto 0;

    color:
        var(--muted);

    font-size: 13px;

    line-height: 1.6;
}


/* ============================================================
   USER MESSAGE
============================================================ */

.user-block {
    display: flex;

    justify-content:
        flex-end;

    margin-bottom: 30px;
}

.user-message {
    width:
        min(
            74%,
            620px
        );
}

.user-label {
    margin:
        0 6px 6px 0;

    text-align: right;

    color:
        var(--muted);

    font-size: 10px;

    font-weight: 650;
}

.user-bubble {
    padding:
        12px 15px;

    border-radius:
        18px
        18px
        4px
        18px;

    background:
        var(--surface-2);

    font-size: 13px;

    line-height: 1.65;

    white-space:
        pre-wrap;
}

.user-reactions {
    display: flex;

    justify-content:
        flex-end;

    gap: 2px;

    margin-top: 5px;
}

.user-reaction {
    width: 28px;
    height: 28px;

    padding: 0;

    border: 0;

    border-radius: 7px;

    background:
        transparent;

    font-size: 14px;
}

.user-reaction:hover,
.user-reaction.active {
    background:
        var(--surface-2);
}


/* ============================================================
   AI ANSWER
============================================================ */

.assistant-block {
    margin-bottom: 34px;
}

.assistant-label {
    margin-bottom: 8px;

    color:
        var(--muted);

    font-size: 10px;

    font-weight: 650;
}

.answer-card {
    border: 0;

    background:
        transparent;
}

.answer-header {
    display: flex;

    align-items: center;

    justify-content:
        space-between;

    gap: 12px;

    margin-bottom: 11px;
}

.answer-header
.small-label {
    display: block;

    color:
        var(--muted);

    font-size: 8px;

    text-transform:
        uppercase;

    letter-spacing:
        .08em;
}

.answer-header strong {
    display: block;

    margin-top: 2px;

    font-size: 12px;
}

.answer-actions {
    display: flex;

    gap: 5px;
}

.answer-actions button {
    padding:
        6px 9px;

    border: 0;

    border-radius: 8px;

    background:
        transparent;

    color:
        var(--muted);

    font-size: 9px;
}

.answer-actions button:hover {
    background:
        var(--surface-2);

    color:
        var(--text);
}

.answer-content {
    font-size: 13px;

    line-height: 1.82;
}

.answer-content p {
    margin:
        0 0 13px;
}

.answer-subheading {
    margin:
        18px 0 7px;

    font-size: 14px;
}

.answer-list {
    margin:
        4px 0 14px;

    padding-left: 20px;
}

.answer-list li {
    margin-bottom: 6px;
}

.answer-content code {
    padding:
        2px 5px;

    border-radius: 6px;

    background:
        var(--surface-2);
}

.citation {
    display: inline-flex;

    padding:
        1px 6px;

    border:
        1px solid
        var(--accent-border);

    border-radius: 999px;

    background:
        var(--accent-soft);

    color:
        var(--accent-2);

    font-size: 9px;

    font-weight: 700;
}

.performance-row {
    display: flex;

    flex-wrap: wrap;

    gap: 10px;

    margin:
        12px 0 13px;

    color:
        var(--muted);

    font-size: 8px;
}


/* ============================================================
   CODE
============================================================ */

.code-wrapper {
    overflow: hidden;

    margin:
        16px 0;

    border:
        1px solid
        var(--border);

    border-radius: 12px;

    background:
        #111216;
}

.code-header {
    display: flex;

    justify-content:
        space-between;

    align-items: center;

    padding:
        7px 10px;

    border-bottom:
        1px solid
        rgba(
            255,
            255,
            255,
            .08
        );

    color: #a5a7b0;

    font-size: 9px;
}

.code-header button {
    padding:
        4px 7px;

    border: 0;

    border-radius: 6px;

    background:
        #20222a;

    color:
        #ececf0;

    font-size: 8px;
}

pre {
    margin: 0;

    padding: 13px;

    overflow: auto;
}

pre code {
    padding:
        0 !important;

    border:
        0 !important;

    background:
        transparent !important;

    color:
        #ececf0 !important;

    font-size:
        11px !important;
}


/* ============================================================
   SOURCES
============================================================ */

.sources-block {
    margin-top: 10px;
}

.sources-heading {
    display: flex;

    justify-content:
        space-between;

    gap: 10px;

    margin-bottom: 8px;
}

.sources-heading strong {
    font-size: 10px;
}

.sources-heading span {
    color:
        var(--muted);

    font-size: 8px;
}

.source-grid {
    display: grid;

    grid-template-columns:
        repeat(
            2,
            minmax(
                0,
                1fr
            )
        );

    gap: 7px;
}

.compact
.source-grid {
    grid-template-columns:
        1fr;
}

.source-card {
    min-width: 0;

    display: block;

    padding:
        9px 10px;

    border:
        1px solid
        var(--border);

    border-radius: 10px;

    background:
        var(--surface);
}

.source-card:hover {
    border-color:
        var(--accent-border);
}

.source-top {
    display: flex;

    justify-content:
        space-between;

    gap: 6px;

    margin-bottom: 6px;
}

.source-number {
    width: 21px;
    height: 21px;

    display: grid;

    place-items: center;

    border-radius: 7px;

    background:
        var(--accent-soft);

    color:
        var(--accent-2);

    font-size: 8px;

    font-weight: 750;
}

.source-score {
    color:
        var(--muted);

    font-size: 7px;
}

.source-card strong {
    display: block;

    font-size: 9px;
}

.source-card small {
    display: block;

    margin-top: 2px;

    color:
        var(--muted);

    font-size: 7px;
}

.source-link {
    display: block;

    margin-top: 5px;

    color:
        var(--accent-2);

    font-size: 8px;
}

.empty-source {
    color:
        var(--muted);

    font-size: 9px;
}


/* ============================================================
   FEEDBACK
============================================================ */

.feedback-row {
    display: flex;

    align-items: center;

    flex-wrap: wrap;

    gap: 5px;

    margin-top: 12px;
}

.feedback-row
> span:first-child {
    color:
        var(--muted);

    font-size: 9px;
}

.feedback-button {
    padding:
        6px 8px;

    border: 0;

    border-radius: 8px;

    background:
        transparent;

    color:
        var(--muted);

    font-size: 9px;
}

.feedback-button:hover,
.feedback-button.active {
    background:
        var(--surface-2);

    color:
        var(--text);
}

.feedback-thanks {
    color:
        var(--accent-2);

    font-size: 8px;
}


/* ============================================================
   COMPARE
============================================================ */

.compare-summary {
    display: grid;

    grid-template-columns:
        repeat(
            4,
            minmax(
                0,
                1fr
            )
        );

    gap: 7px;

    margin:
        0 0 22px;
}

.compare-summary div {
    padding:
        9px 10px;

    border:
        1px solid
        var(--border);

    border-radius: 10px;

    background:
        var(--surface);
}

.compare-summary span {
    display: block;

    color:
        var(--muted);

    font-size: 7px;
}

.compare-summary strong {
    display: block;

    margin-top: 3px;

    color:
        var(--accent-2);

    font-size: 11px;
}

.compare-grid {
    display: grid;

    grid-template-columns:
        repeat(
            2,
            minmax(
                0,
                1fr
            )
        );

    gap: 16px;
}

.compare-grid
.answer-card {
    padding: 13px;

    border:
        1px solid
        var(--border);

    border-radius: 14px;

    background:
        var(--surface);
}


/* ============================================================
   COMPOSER
============================================================ */

.composer-shell {
    position: fixed;

    left: 260px;

    right: 0;

    bottom: 0;

    z-index: 35;

    padding:
        16px 20px 20px;

    background:
        linear-gradient(
            180deg,
            transparent 0%,
            var(--page) 28%
        );
}

body.empty-chat
.composer-shell {
    padding-bottom: 22px;
}

.composer {
    width:
        min(
            760px,
            calc(
                100% - 16px
            )
        );

    margin:
        0 auto;

    padding:
        8px 10px 9px;

    border:
        1px solid
        var(--border);

    border-radius: 24px;

    background:
        var(--surface);
}

.composer textarea {
    width: 100%;

    min-height: 50px;

    max-height: 150px;

    resize: none;

    padding:
        10px 9px 7px;

    border: 0;

    outline: 0;

    background:
        transparent;

    color:
        var(--text);

    font-size: 13px;

    line-height: 1.5;
}

.composer textarea::placeholder {
    color:
        var(--muted);
}

.composer-bottom {
    display: flex;

    align-items: center;

    justify-content:
        space-between;

    gap: 9px;
}

.composer-left {
    display: flex;

    align-items: center;

    gap: 5px;
}

.method-select,
.composer-button {
    height: 31px;

    padding:
        0 9px;

    border: 0;

    border-radius: 9px;

    background:
        transparent;

    color:
        var(--muted);

    font-size: 9px;
}

.method-select:hover,
.composer-button:hover {
    background:
        var(--surface-2);

    color:
        var(--text);
}

.send-button {
    width: 34px;
    height: 34px;

    display: grid;

    place-items: center;

    border: 0;

    border-radius: 50%;

    background:
        var(--accent);

    color: white;

    font-size: 17px;
}

.send-button:hover {
    background:
        var(--accent-2);
}

.composer-note {
    margin:
        6px auto 0;

    text-align: center;

    color:
        var(--muted);

    font-size: 7px;
}


/* ============================================================
   LOADING
============================================================ */

.loading-overlay {
    display: none;

    position: fixed;

    inset: 0;

    z-index: 999;

    place-items: center;

    background:
        rgba(
            0,
            0,
            0,
            .44
        );

    backdrop-filter:
        blur(4px);
}

.loading-overlay.active {
    display: grid;
}

.loading-card {
    width:
        min(
            320px,
            calc(
                100% - 34px
            )
        );

    padding: 22px;

    border:
        1px solid
        var(--border);

    border-radius: 16px;

    background:
        var(--surface);

    text-align: center;
}

.spinner {
    width: 34px;
    height: 34px;

    margin:
        0 auto 11px;

    border:
        3px solid
        var(--border);

    border-top-color:
        var(--accent-2);

    border-radius: 50%;

    animation:
        spin
        .8s
        linear
        infinite;
}

@keyframes spin {
    to {
        transform:
            rotate(
                360deg
            );
    }
}

.loading-card strong {
    display: block;

    font-size: 11px;
}

.loading-card span {
    display: block;

    margin-top: 4px;

    color:
        var(--muted);

    font-size: 8px;
}


/* ============================================================
   ABOUT RESULTS LOGIN
============================================================ */

.page {
    width:
        min(
            940px,
            calc(
                100% - 38px
            )
        );

    margin:
        0 auto;

    padding:
        34px 0 80px;
}

.page h1 {
    margin:
        0 0 8px;

    font-size: 30px;
}

.page > p {
    max-width: 700px;

    margin: 0;

    color:
        var(--muted);

    font-size: 12px;

    line-height: 1.7;
}

.info-grid,
.metric-grid,
.graph-grid {
    display: grid;

    gap: 10px;

    margin-top: 20px;
}

.info-grid,
.graph-grid {
    grid-template-columns:
        repeat(
            2,
            minmax(
                0,
                1fr
            )
        );
}

.metric-grid {
    grid-template-columns:
        repeat(
            4,
            minmax(
                0,
                1fr
            )
        );
}

.info-card,
.metric-card,
.graph-card,
.login-card {
    padding: 15px;

    border:
        1px solid
        var(--border);

    border-radius: 14px;

    background:
        var(--surface);
}

.info-card h2 {
    margin:
        0 0 6px;

    font-size: 13px;
}

.info-card p {
    margin: 0;

    color:
        var(--muted);

    font-size: 10px;

    line-height: 1.6;
}

.metric-card span {
    display: block;

    color:
        var(--muted);

    font-size: 8px;
}

.metric-card strong {
    display: block;

    margin-top: 4px;

    font-size: 16px;
}

.graph-card img {
    width: 100%;

    display: block;

    border-radius: 9px;

    background: white;
}

.login-card {
    width:
        min(
            420px,
            100%
        );

    margin:
        50px auto 0;
}

.login-card h2 {
    margin:
        0 0 6px;
}

.login-card p {
    margin:
        0 0 16px;

    color:
        var(--muted);

    font-size: 10px;

    line-height: 1.6;
}

.login-field {
    display: grid;

    gap: 5px;

    margin-bottom: 10px;
}

.login-field label {
    color:
        var(--muted);

    font-size: 9px;
}

.login-field input {
    width: 100%;

    padding:
        10px 11px;

    border:
        1px solid
        var(--border);

    border-radius: 10px;

    outline: 0;

    background:
        var(--surface-2);
}

.login-field input:focus {
    border-color:
        var(--accent-border);
}

.login-submit {
    width: 100%;

    padding:
        10px 12px;

    border: 0;

    border-radius: 10px;

    background:
        var(--accent);

    color: white;

    font-weight: 650;
}

.error-card {
    padding: 14px;

    border:
        1px solid
        rgba(
            255,
            125,
            141,
            .25
        );

    border-radius: 12px;

    background:
        rgba(
            255,
            125,
            141,
            .07
        );

    color:
        var(--danger);

    font-size: 10px;
}


/* ============================================================
   RESPONSIVE
============================================================ */

@media (
    max-width: 920px
) {

    .app-shell {
        grid-template-columns:
            1fr;
    }

    .sidebar {
        transform:
            translateX(
                -100%
            );

        transition:
            transform
            .2s ease;
    }

    .sidebar.open {
        transform:
            translateX(
                0
            );
    }

    .main-shell {
        grid-column: 1;
    }

    .composer-shell {
        left: 0;
    }

    .mobile-menu {
        display: grid;
    }
}


@media (
    max-width: 700px
) {

    .chat-area {
        width:
            calc(
                100% - 24px
            );
    }

    .source-grid,
    .compare-grid,
    .compare-summary,
    .info-grid,
    .metric-grid,
    .graph-grid {
        grid-template-columns:
            1fr;
    }

    .user-message {
        width: 88%;
    }

    .topbar-title {
        font-size: 12px;
    }

    .topbar-right {
        gap: 2px;
    }

    .top-button {
        padding:
            0 7px;

        font-size: 9px;
    }

    .signin-top {
        padding:
            0 9px;
    }
}
"""
# ============================================================
# JAVASCRIPT
# ============================================================

JS = r"""
const HISTORY_KEY =
    "fastapi_assistant_history";

const THEME_KEY =
    "fastapi_assistant_theme";

const LAST_QUESTION_KEY =
    "fastapi_last_question";

const LAST_METHOD_KEY =
    "fastapi_last_method";


const form =
    document.getElementById(
        "question-form"
    );

const questionInput =
    document.getElementById(
        "question-input"
    );

const methodSelect =
    document.getElementById(
        "retrieval-method"
    );

const historyContainer =
    document.getElementById(
        "history-container"
    );

const historySearch =
    document.getElementById(
        "history-search-input"
    );

const loadingOverlay =
    document.getElementById(
        "loading-overlay"
    );


function getHistory() {

    try {

        return JSON.parse(
            localStorage.getItem(
                HISTORY_KEY
            )
            || "[]"
        );

    } catch {

        return [];

    }
}


function saveQuestion(
    question
) {

    if (!question) {
        return;
    }


    let history =
        getHistory()
            .filter(
                item =>
                    item !== question
            );


    history.unshift(
        question
    );


    localStorage.setItem(
        HISTORY_KEY,
        JSON.stringify(
            history.slice(
                0,
                20
            )
        )
    );


    renderHistory();
}


function renderHistory(
    filterText = ""
) {

    if (!historyContainer) {
        return;
    }


    const filter =
        filterText
            .trim()
            .toLowerCase();


    const history =
        getHistory()
            .filter(
                question =>
                    question
                        .toLowerCase()
                        .includes(
                            filter
                        )
            );


    historyContainer.innerHTML =
        "";


    if (!history.length) {

        historyContainer.innerHTML =
            '<div class="history-empty">'
            + 'No recent chats yet.'
            + '</div>';

        return;
    }


    history.forEach(
        question => {

            const button =
                document.createElement(
                    "button"
                );


            button.type =
                "button";


            button.className =
                "history-item";


            button.textContent =
                question;


            button.title =
                question;


            button.onclick =
                () => {

                    if (
                        questionInput
                    ) {

                        questionInput.value =
                            question;

                        questionInput.focus();
                    }


                    closeSidebar();
                };


            historyContainer.appendChild(
                button
            );
        }
    );
}


function toggleHistorySearch() {

    const searchBox =
        document.getElementById(
            "chat-search"
        );


    if (!searchBox) {
        return;
    }


    searchBox.classList.toggle(
        "open"
    );


    const input =
        document.getElementById(
            "history-search-input"
        );


    if (
        searchBox.classList.contains(
            "open"
        )
        &&
        input
    ) {

        input.focus();
    }
}


function clearHistory() {

    localStorage.removeItem(
        HISTORY_KEY
    );


    renderHistory();
}


function newChat() {

    window.location.href =
        "/";
}


function focusComposer() {

    if (!questionInput) {

        window.location.href =
            "/";

        return;
    }


    questionInput.focus();
}


function clearQuestion() {

    if (!questionInput) {
        return;
    }


    questionInput.value =
        "";


    questionInput.focus();
}


function toggleSidebar() {

    document
        .getElementById(
            "sidebar"
        )
        ?.classList
        .toggle(
            "open"
        );
}


function closeSidebar() {

    document
        .getElementById(
            "sidebar"
        )
        ?.classList
        .remove(
            "open"
        );
}


function applyTheme(
    theme
) {

    document.body.setAttribute(
        "data-theme",
        theme
    );


    localStorage.setItem(
        THEME_KEY,
        theme
    );


    const button =
        document.getElementById(
            "theme-button"
        );


    if (button) {

        button.textContent =
            theme === "dark"
            ? "☀ Light"
            : "☾ Dark";
    }
}


function toggleTheme() {

    const current =
        document.body.getAttribute(
            "data-theme"
        )
        || "dark";


    applyTheme(
        current === "dark"
        ? "light"
        : "dark"
    );
}


function selectUserReaction(
    button
) {

    const row =
        button.closest(
            ".user-reactions"
        );


    if (!row) {
        return;
    }


    row
        .querySelectorAll(
            ".user-reaction"
        )
        .forEach(
            item => {

                item.classList.remove(
                    "active"
                );
            }
        );


    button.classList.add(
        "active"
    );
}


function setHelpful(
    button,
    value
) {

    const row =
        button.closest(
            ".feedback-row"
        );


    if (!row) {
        return;
    }


    row
        .querySelectorAll(
            ".feedback-button"
        )
        .forEach(
            item => {

                item.classList.remove(
                    "active"
                );
            }
        );


    button.classList.add(
        "active"
    );


    const thanks =
        row.querySelector(
            ".feedback-thanks"
        );


    if (thanks) {

        thanks.textContent =
            value === "yes"
            ? "Thanks for your feedback ✓"
            : "Thanks — this helps improve the assistant.";
    }
}


async function copyAnswer(
    id,
    button
) {

    const element =
        document.getElementById(
            id
        );


    if (!element) {
        return;
    }


    try {

        await navigator
            .clipboard
            .writeText(
                element.innerText
            );


        const original =
            button.innerText;


        button.innerText =
            "Copied";


        setTimeout(
            () => {

                button.innerText =
                    original;
            },
            1000
        );

    } catch (error) {

        console.error(
            error
        );
    }
}


async function copyCode(
    button
) {

    const code =
        button
            .closest(
                ".code-wrapper"
            )
            ?.querySelector(
                "code"
            );


    if (!code) {
        return;
    }


    try {

        await navigator
            .clipboard
            .writeText(
                code.innerText
            );


        const original =
            button.innerText;


        button.innerText =
            "Copied";


        setTimeout(
            () => {

                button.innerText =
                    original;
            },
            1000
        );

    } catch (error) {

        console.error(
            error
        );
    }
}


function regenerateLastQuestion() {

    const question =
        localStorage.getItem(
            LAST_QUESTION_KEY
        );


    const method =
        localStorage.getItem(
            LAST_METHOD_KEY
        )
        || "semantic";


    if (
        !question
        ||
        !form
        ||
        !questionInput
    ) {
        return;
    }


    questionInput.value =
        question;


    if (methodSelect) {

        methodSelect.value =
            method;
    }


    form.requestSubmit();
}


if (historySearch) {

    historySearch.addEventListener(
        "input",
        event => {

            renderHistory(
                event.target.value
            );
        }
    );
}


if (form) {

    form.addEventListener(
        "submit",
        () => {

            const question =
                questionInput
                    .value
                    .trim();


            const method =
                methodSelect
                    ?.value
                || "semantic";


            saveQuestion(
                question
            );


            localStorage.setItem(
                LAST_QUESTION_KEY,
                question
            );


            localStorage.setItem(
                LAST_METHOD_KEY,
                method
            );


            loadingOverlay
                ?.classList
                .add(
                    "active"
                );
        }
    );
}


if (questionInput) {

    questionInput.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter"
                &&
                !event.shiftKey
            ) {

                event.preventDefault();


                if (
                    questionInput
                        .value
                        .trim()
                ) {

                    form?.requestSubmit();
                }
            }
        }
    );
}


applyTheme(
    localStorage.getItem(
        THEME_KEY
    )
    || "dark"
);


renderHistory();
"""


# ============================================================
# SIDEBAR
# ============================================================

def sidebar_html():

    return """
    <aside
        class="sidebar"
        id="sidebar"
    >

        <div class="sidebar-head">

            <div class="sidebar-name">
                FastAPI Assistant
            </div>

            <button
                type="button"
                class="sidebar-icon-button"
                onclick="closeSidebar()"
                title="Close sidebar"
            >
                ◫
            </button>

        </div>


        <nav class="side-nav">

            <button
                type="button"
                class="
                    side-action
                    active
                "
                onclick="newChat()"
            >

                <span class="side-symbol">
                    ✎
                </span>

                <span>
                    New chat
                </span>

            </button>


            <button
                type="button"
                class="side-action"
                onclick="
                    toggleHistorySearch()
                "
            >

                <span class="side-symbol">
                    ⌕
                </span>

                <span>
                    Search chats
                </span>

            </button>


            <div
                class="chat-search"
                id="chat-search"
            >

                <input
                    type="text"
                    id="history-search-input"
                    placeholder="Search history..."
                >

            </div>


            <a
                href="/about"
                class="side-link"
            >

                <span class="side-symbol">
                    ⓘ
                </span>

                <span>
                    About
                </span>

            </a>


            <a
                href="/results"
                class="side-link"
            >

                <span class="side-symbol">
                    ▥
                </span>

                <span>
                    Results
                </span>

            </a>

        </nav>


        <div class="side-section-title">
            Recents
        </div>


        <div
            class="history-list"
            id="history-container"
        ></div>


        <div class="sidebar-bottom">

            <a
                href="/login"
                class="profile-row"
            >

                <div class="profile-avatar">
                    G
                </div>

                <div class="profile-copy">

                    <strong>
                        Guest
                    </strong>

                    <span>
                        Sign in to save chats
                    </span>

                </div>

            </a>

        </div>

    </aside>
    """


# ============================================================
# TOP BAR
# ============================================================

def topbar_html(
    title="FastAPI Assistant"
):

    return f"""
    <header class="topbar">

        <div class="topbar-left">

            <button
                type="button"
                class="mobile-menu"
                onclick="toggleSidebar()"
                title="Menu"
                aria-label="Open menu"
            >
                ☰
            </button>


            <div class="topbar-title">
                {html.escape(title)}
            </div>

        </div>


        <div class="topbar-right">

            <button
                type="button"
                class="top-button"
                onclick="focusComposer()"
            >
                ⌕ Search
            </button>


            <button
                type="button"
                class="top-button"
                id="theme-button"
                onclick="toggleTheme()"
            >
                ☀ Light
            </button>


            <a
                href="/login"
                class="
                    top-button
                    signin-top
                "
            >
                Sign in
            </a>

        </div>

    </header>
    """


# ============================================================
# DOCUMENT
# ============================================================

def document(
    content,
    title=APP_TITLE,
    body_class="",
):

    safe_title = html.escape(
        title
    )

    return f"""
    <!DOCTYPE html>

    <html lang="en">

    <head>

        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="
                width=device-width,
                initial-scale=1.0
            "
        >

        <title>
            {safe_title}
        </title>

        <style>
            {CSS}
        </style>
        
        <link
    rel="stylesheet"
    href="/static/css/history.css"
        >
    </head>


    <body
        data-theme="dark"
        class="{body_class}"
    >

        <div class="app-shell">

            {sidebar_html()}


            <main class="main-shell">

                {
                    topbar_html(
                        title
                    )
                }

                {content}

            </main>

        </div>


        <script>
    {JS}
</script>

<script src="/static/js/app.js"></script>
<script src="/static/js/feedback.js"></script>
<script src="/static/js/search_chats.js"></script>
<script src="/static/js/regenerate.js"></script>

</body>

    </html>
    """


# ============================================================
# USER MESSAGE
# ============================================================

def user_message_html(
    question
):

    return f"""
    <section class="user-block">

        <div class="user-message">

            <div class="user-label">
                You
            </div>


            <div class="user-bubble">
                {html.escape(question)}
            </div>


            <div class="user-reactions">

                <button
                    type="button"
                    class="user-reaction"
                    onclick="
                        selectUserReaction(
                            this
                        )
                    "
                    title="Good"
                >
                    🙂
                </button>


                <button
                    type="button"
                    class="user-reaction"
                    onclick="
                        selectUserReaction(
                            this
                        )
                    "
                    title="Like"
                >
                    👍
                </button>


                <button
                    type="button"
                    class="user-reaction"
                    onclick="
                        selectUserReaction(
                            this
                        )
                    "
                    title="Dislike"
                >
                    👎
                </button>

            </div>

        </div>

    </section>
    """


# ============================================================
# COMPOSER
# ============================================================

def composer_html(
    method="semantic"
):

    semantic_selected = (
        "selected"
        if method == "semantic"
        else ""
    )

    bm25_selected = (
        "selected"
        if method == "bm25"
        else ""
    )

    compare_selected = (
        "selected"
        if method == "compare"
        else ""
    )

    return f"""
    <div class="composer-shell">

        <form
            method="post"
            action="/"
            class="composer"
            id="question-form"
        >

            <textarea
                name="question"
                id="question-input"
                required
                placeholder="Ask FastAPI..."
            ></textarea>


            <div class="composer-bottom">

                <div class="composer-left">

                    <select
                        name="retrieval_method"
                        id="retrieval-method"
                        class="method-select"
                    >

                        <option
                            value="semantic"
                            {semantic_selected}
                        >
                            Semantic
                        </option>

                        <option
                            value="bm25"
                            {bm25_selected}
                        >
                            BM25
                        </option>

                        <option
                            value="compare"
                            {compare_selected}
                        >
                            Compare
                        </option>

                    </select>


                    <button
                        type="button"
                        class="composer-button"
                        onclick="clearQuestion()"
                    >
                        Clear
                    </button>

                </div>


                <button
                    type="submit"
                    class="send-button"
                    title="Send"
                >
                    ↑
                </button>

            </div>

        </form>


        <div class="composer-note">
            Answers are grounded in official
            FastAPI documentation.
        </div>

    </div>
    """


# ============================================================
# HOME PAGE
# ============================================================

def home_page(
    question="",
    method="semantic",
    result=None,
    compare_results=None,
    error=None,
):

    if error:

        question_html = (
            user_message_html(
                question
            )
            if question
            else ""
        )

        conversation = f"""
        {question_html}

        <section class="assistant-block">

            <div class="assistant-label">
                FastAPI Assistant
            </div>

            <div class="error-card">

                <strong>
                    Unable to generate answer
                </strong>

                <div
                    style="
                        margin-top:5px;
                    "
                >
                    {html.escape(error)}
                </div>

            </div>

        </section>
        """

    elif compare_results:

        semantic_result = (
            compare_results[0]
        )

        bm25_result = (
            compare_results[1]
        )

        semantic_card = result_card(
            semantic_result,
            "semantic-answer",
            compact=True,
        )

        bm25_card = result_card(
            bm25_result,
            "bm25-answer",
            compact=True,
        )

        conversation = f"""
        {
            user_message_html(
                question
            )
        }

        {
            compare_summary_card(
                semantic_result,
                bm25_result,
            )
        }

        <section class="assistant-block">

            <div class="assistant-label">
                FastAPI Assistant ·
                Compare mode
            </div>


            <div class="compare-grid">

                {semantic_card}

                {bm25_card}

            </div>

        </section>
        """

    elif result:

        conversation = f"""
        {
            user_message_html(
                question
            )
        }

        <section class="assistant-block">

            <div class="assistant-label">
                FastAPI Assistant
            </div>

            {
                result_card(
                    result,
                    "main-answer",
                )
            }

        </section>
        """

    else:

        conversation = """
        <section class="empty-state">

            <h1>
                How can I help?
            </h1>

            <p>
                Ask a question about FastAPI
                and get an answer grounded in
                the official documentation.
            </p>

        </section>
        """

    content = f"""
    <div
        class="loading-overlay"
        id="loading-overlay"
    >

        <div class="loading-card">

            <div class="spinner">
            </div>

            <strong>
                Searching documentation...
            </strong>

            <span>
                Retrieving sources and
                generating an answer.
            </span>

        </div>

    </div>


    <section class="chat-area">

        {conversation}

    </section>


    {
        composer_html(
            method
        )
    }
    """

    body_class = (
        "empty-chat"
        if not any(
            [
                question,
                result,
                compare_results,
                error,
            ]
        )
        else ""
    )

    return document(
        content,
        APP_TITLE,
        body_class=body_class,
    )


# ============================================================
# ABOUT
# ============================================================

def about_page():

    content = """
    <section class="page">

        <h1>
            About the project
        </h1>

        <p>
            This project investigates a
            RAG-based technical documentation
            assistant using official FastAPI
            documentation and compares semantic
            retrieval with BM25.
        </p>


        <div class="info-grid">

            <article class="info-card">

                <h2>
                    Documentation corpus
                </h2>

                <p>
                    Official English FastAPI
                    documentation is collected,
                    cleaned, chunked and stored
                    with source URLs.
                </p>

            </article>


            <article class="info-card">

                <h2>
                    Semantic retrieval
                </h2>

                <p>
                    Sentence embeddings retrieve
                    chunks according to semantic
                    similarity between the
                    question and documentation.
                </p>

            </article>


            <article class="info-card">

                <h2>
                    BM25 retrieval
                </h2>

                <p>
                    BM25 provides the
                    keyword-based baseline over
                    the same documentation corpus.
                </p>

            </article>


            <article class="info-card">

                <h2>
                    Grounded generation
                </h2>

                <p>
                    Retrieved chunks are passed
                    to the language model, which
                    answers using those sources.
                </p>

            </article>

        </div>

    </section>
    """

    return document(
        content,
        "About · FastAPI Assistant",
    )


# ============================================================
# RESULTS
# ============================================================

def load_results():

    if not RESULTS_FILE.exists():
        return None

    try:

        return json.loads(
            RESULTS_FILE.read_text(
                encoding="utf-8"
            )
        )

    except Exception as exc:

        print(
            "Could not load results:",
            repr(exc),
        )

        return None


def results_page():

    data = load_results()

    if not data:

        return document(
            """
            <section class="page">

                <div class="error-card">
                    Evaluation results
                    could not be loaded.
                </div>

            </section>
            """,

            "Results · FastAPI Assistant",
        )

    semantic = (
        data[
            "retrieval_results"
        ]["semantic"]
    )

    bm25 = (
        data[
            "retrieval_results"
        ]["bm25"]
    )

    semantic_answer = (
        data[
            "answer_quality_results"
        ]["semantic"]
    )

    bm25_answer = (
        data[
            "answer_quality_results"
        ]["bm25"]
    )

    metrics = [
        (
            "Semantic Top-1",
            f'{semantic["hit_at_1"] * 100:.0f}%',
        ),
        (
            "BM25 Top-1",
            f'{bm25["hit_at_1"] * 100:.0f}%',
        ),
        (
            "Semantic Top-3",
            f'{semantic["hit_at_3"] * 100:.0f}%',
        ),
        (
            "BM25 Top-3",
            f'{bm25["hit_at_3"] * 100:.0f}%',
        ),
        (
            "Semantic Top-5",
            f'{semantic["hit_at_5"] * 100:.0f}%',
        ),
        (
            "BM25 Top-5",
            f'{bm25["hit_at_5"] * 100:.0f}%',
        ),
        (
            "Semantic correctness",
            f'{semantic_answer["correctness_percentage"]:.1f}%',
        ),
        (
            "BM25 correctness",
            f'{bm25_answer["correctness_percentage"]:.1f}%',
        ),
    ]

    metric_html = "".join(
        f"""
        <div class="metric-card">

            <span>
                {html.escape(label)}
            </span>

            <strong>
                {html.escape(value)}
            </strong>

        </div>
        """
        for label, value
        in metrics
    )

    graph_names = [
        "retrieval_accuracy.png",
        "mean_reciprocal_rank.png",
        "answer_correctness.png",
        "retrieval_response_time.png",
        "total_response_time.png",
    ]

    graph_html = "".join(
        f"""
        <div class="graph-card">

            <img
                src="/graphs/{filename}"
                alt="{html.escape(filename)}"
            >

        </div>
        """
        for filename
        in graph_names
        if (
            GRAPHS_DIR
            / filename
        ).exists()
    )

    return document(
        f"""
        <section class="page">

            <h1>
                Evaluation results
            </h1>

            <p>
                Candidate evaluation
                comparing Semantic and BM25
                retrieval on the FastAPI
                documentation corpus.
            </p>


            <div class="metric-grid">
                {metric_html}
            </div>


            <div class="graph-grid">
                {graph_html}
            </div>

        </section>
        """,

        "Results · FastAPI Assistant",
    )


# ============================================================
# ROUTES
# ============================================================

@app.get(
    "/",
    response_class=HTMLResponse,
)
async def home():

    return home_page()


@app.post(
    "/",
    response_class=HTMLResponse,
)
async def ask_question(
    request: Request,
    question: str = Form(...),
    retrieval_method: str = Form(
        "semantic"
    ),
    chat_id: int | None = Form(
        None
    ),
):

    question = question.strip()

    if not question:

        return home_page(
            error=(
                "Please enter a question."
            )
        )

    if (
        retrieval_method
        not in {
            "semantic",
            "bm25",
            "compare",
        }
    ):

        retrieval_method = (
            "semantic"
        )

    try:

        # ====================================================
        # CURRENT USER
        # ====================================================

        user = get_logged_in_user(
            request
        )


        # ====================================================
        # COMPARE MODE
        # ====================================================

        if (
            retrieval_method
            == "compare"
        ):

            semantic_result = run_rag(
                question,
                "semantic",
            )

            bm25_result = run_rag(
                question,
                "bm25",
            )


            # -----------------------------------------------
            # Save conversation for signed-in users
            # -----------------------------------------------

            if user:

                try:

                   save_compare_chat(
    user_id=user["id"],
    question=question,
    semantic_result=
        semantic_result,
    bm25_result=
        bm25_result,
    chat_id=chat_id,
)

                except Exception as save_error:

                    print(
                        "Could not save chat:",
                        repr(save_error),
                    )


            return home_page(
                question=question,
                method="compare",
                compare_results=[
                    semantic_result,
                    bm25_result,
                ],
            )


        # ====================================================
        # SEMANTIC OR BM25
        # ====================================================

        result = run_rag(
            question,
            retrieval_method,
        )


        # ----------------------------------------------------
        # Save conversation for signed-in users
        # ----------------------------------------------------

        if user:

            try:

               save_rag_chat(
    user_id=user["id"],
    question=question,
    result=result,
    chat_id=chat_id,
)

            except Exception as save_error:

                print(
                    "Could not save chat:",
                    repr(save_error),
                )


        return home_page(
            question=question,
            method=retrieval_method,
            result=result,
        )


    except Exception as exc:

        print(
            "RAG request error:",
            repr(exc),
        )

        return home_page(
            question=question,
            method=retrieval_method,
            error=friendly_error(
                exc
            ),
        )

    question = question.strip()

    if not question:

        return home_page(
            error=(
                "Please enter a question."
            )
        )

    if (
        retrieval_method
        not in {
            "semantic",
            "bm25",
            "compare",
        }
    ):

        retrieval_method = (
            "semantic"
        )

    try:

        if (
            retrieval_method
            == "compare"
        ):

            semantic_result = run_rag(
                question,
                "semantic",
            )

            bm25_result = run_rag(
                question,
                "bm25",
            )

            return home_page(
                question=question,
                method="compare",
                compare_results=[
                    semantic_result,
                    bm25_result,
                ],
            )

        result = run_rag(
            question,
            retrieval_method,
        )

        return home_page(
            question=question,
            method=retrieval_method,
            result=result,
        )

    except Exception as exc:

        print(
            "RAG request error:",
            repr(exc),
        )

        return home_page(
            question=question,
            method=retrieval_method,
            error=friendly_error(
                exc
            ),
        )


@app.get(
    "/about",
    response_class=HTMLResponse,
)
async def about():

    return about_page()


@app.get(
    "/results",
    response_class=HTMLResponse,
)
async def results():

    return results_page()


@app.get(
    "/graphs/{filename}",
)
async def graph_file(
    filename: str,
):

    allowed = {
        "retrieval_accuracy.png",
        "mean_reciprocal_rank.png",
        "answer_correctness.png",
        "retrieval_response_time.png",
        "total_response_time.png",
    }

    if filename not in allowed:

        raise HTTPException(
            status_code=404
        )

    path = (
        GRAPHS_DIR
        / filename
    )

    if not path.exists():

        raise HTTPException(
            status_code=404
        )

    return FileResponse(
        path
    )