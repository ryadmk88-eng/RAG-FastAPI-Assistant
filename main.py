import html
import json
import os
import re
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from bm25_search import build_bm25
from semantic_search import MODEL_NAME, load_data


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

APP_TITLE = "FastAPI Docs Assistant"
TOP_K = 5
LLM_MODEL = "gpt-6-luna"

BASE_DIR = Path(__file__).resolve().parent

RESULTS_FILE = (
    BASE_DIR
    / "results"
    / "final_results_summary.json"
)

GRAPHS_DIR = (
    BASE_DIR
    / "results"
    / "graphs"
)


# ============================================================
# LOAD RAG COMPONENTS ONCE
# ============================================================

print("Loading FastAPI documentation corpus...")

chunks, embeddings = load_data()

print("Loading semantic embedding model...")

embedding_model = SentenceTransformer(
    MODEL_NAME
)

print("Building BM25 index...")

bm25_index = build_bm25(chunks)

print("RAG system ready.")


api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print(
        "WARNING: OPENAI_API_KEY "
        "was not found in .env"
    )

client = OpenAI(
    api_key=api_key
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title=APP_TITLE,
    description=(
        "RAG-based technical documentation "
        "assistant for FastAPI."
    ),
)


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

    query_embedding = (
        embedding_model.encode(
            query,
            normalize_embeddings=True,
        )
    )

    scores = (
        embeddings
        @ query_embedding
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


def bm25_search(
    query,
    top_k=TOP_K,
):
    start = time.perf_counter()

    query_tokens = tokenize(query)

    scores = bm25_index.get_scores(
        query_tokens
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
# BUILD LLM CONTEXT
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

        source_number = (
            source_numbers[url]
        )

        current_score = float(
            chunk.get(
                "retrieval_score",
                0,
            )
        )

        previous_score = (
            source_data[
                source_number
            ]["score"]
        )

        if (
            current_score
            > previous_score
        ):
            source_data[
                source_number
            ]["score"] = (
                current_score
            )

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
# LLM ANSWER GENERATION
# ============================================================

def generate_answer(
    question,
    retrieved_chunks,
):
    context, source_data = (
        build_context(
            retrieved_chunks
        )
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
            "The model did not return an "
            "answer for this request."
        )

    return (
        answer,
        source_data,
        generation_ms,
    )


# ============================================================
# RUN ONE COMPLETE RAG REQUEST
# ============================================================

def run_rag(
    question,
    method,
):
    total_start = (
        time.perf_counter()
    )

    if method == "bm25":
        (
            retrieved_chunks,
            retrieval_ms,
        ) = bm25_search(question)

        label = (
            "BM25 Keyword Search"
        )

    else:
        (
            retrieved_chunks,
            retrieval_ms,
        ) = semantic_search(
            question
        )

        label = (
            "Semantic / Vector Search"
        )

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
        "method":
            method,

        "label":
            label,

        "answer":
            answer,

        "sources":
            source_data,

        "retrieval_ms":
            retrieval_ms,

        "generation_ms":
            generation_ms,

        "total_ms":
            total_ms,
    }


# ============================================================
# ANSWER FORMATTING
# ============================================================

def format_text_section(text):
    escaped = html.escape(text)

    # Inline code
    escaped = re.sub(
        r"`([^`\n]+)`",
        r"<code>\1</code>",
        escaped,
    )

    # Source citations
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
                output.append(
                    "</ul>"
                )

                in_list = False

            continue

        # Markdown heading
        heading_match = re.match(
            r"^#{1,4}\s+(.+)$",
            stripped,
        )

        if heading_match:
            if in_list:
                output.append(
                    "</ul>"
                )

                in_list = False

            output.append(
                (
                    '<h3 class="answer-subheading">'
                    f"{heading_match.group(1)}"
                    "</h3>"
                )
            )

            continue

        # Bold markdown
        stripped = re.sub(
            r"\*\*(.+?)\*\*",
            r"<strong>\1</strong>",
            stripped,
        )

        # Bullet list
        if stripped.startswith(
            ("- ", "* ")
        ):
            if not in_list:
                output.append(
                    '<ul class="answer-list">'
                )

                in_list = True

            output.append(
                (
                    "<li>"
                    f"{stripped[2:]}"
                    "</li>"
                )
            )

            continue

        # Numbered list
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
                (
                    "<li>"
                    f"{numbered.group(1)}"
                    "</li>"
                )
            )

            continue

        if in_list:
            output.append(
                "</ul>"
            )

            in_list = False

        output.append(
            f"<p>{stripped}</p>"
        )

    if in_list:
        output.append(
            "</ul>"
        )

    return "\n".join(output)


def format_answer(answer):
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

        # Code block
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


def extract_cited_sources(answer):
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
# SOURCE CARDS
# ============================================================

def build_source_cards(
    answer,
    source_data,
    method,
):
    cards = []

    cited_numbers = (
        extract_cited_sources(
            answer
        )
    )

    for number in cited_numbers:
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
                    {source_url}
                </small>

                <span class="source-link">
                    Open documentation ↗
                </span>

            </a>
            """
        )

    if not cards:
        return """
        <div class="empty-card">
            The answer did not contain
            any source citations.
        </div>
        """

    return "\n".join(cards)


# ============================================================
# FRIENDLY ERROR MESSAGES
# ============================================================

def friendly_error(exception):
    message = str(exception).lower()

    if (
        "insufficient_quota"
        in message
        or "quota"
        in message
        or "billing"
        in message
    ):
        return (
            "The AI service currently has "
            "no available API credit."
        )

    if (
        "rate limit"
        in message
        or "rate_limit"
        in message
    ):
        return (
            "The AI service is receiving "
            "too many requests. "
            "Please try again."
        )

    if (
        "timeout"
        in message
        or "timed out"
        in message
    ):
        return (
            "The request took too long. "
            "Please try again."
        )

    if (
        "api key"
        in message
        or "authentication"
        in message
        or "unauthorized"
        in message
    ):
        return (
            "The AI service could not "
            "authenticate. Check the "
            "server configuration."
        )

    if "connection" in message:
        return (
            "The assistant could not connect "
            "to the AI service. "
            "Please try again."
        )

    return (
        "The assistant could not complete "
        "this request. Please try again."
    )


# ============================================================
# RESULT CARD
# ============================================================

def result_card(
    result,
    card_id,
    compact=False,
):
    answer_html = format_answer(
        result["answer"]
    )

    sources_html = (
        build_source_cards(
            result["answer"],
            result["sources"],
            result["method"],
        )
    )

    compact_class = (
        " compact"
        if compact
        else ""
    )

    # Format numbers BEFORE HTML.
    # This avoids the previous
    # ValueError formatting bug.
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
        str(result["label"])
    )

    return f"""
    <article
        class="answer-card{compact_class}"
    >

        <div class="answer-heading">

            <div>

                <span class="eyebrow">
                    Retrieval method
                </span>

                <h2>
                    {method_label}
                </h2>

            </div>

            <button
                type="button"
                class="outline-button"
                onclick="copyAnswer('{card_id}', this)"
            >
                Copy answer
            </button>

        </div>


        <div class="stats">

            <div class="stat">

                <span>
                    Retrieval
                </span>

                <strong>
                    {retrieval_time}
                </strong>

            </div>


            <div class="stat">

                <span>
                    Generation
                </span>

                <strong>
                    {generation_time}
                </strong>

            </div>


            <div class="stat">

                <span>
                    Total response
                </span>

                <strong>
                    {total_time}
                </strong>

            </div>

        </div>


        <div
            class="answer-content"
            id="{card_id}"
        >
            {answer_html}
        </div>


        <div class="sources-block">

            <div class="sources-heading">

                <div>

                    <span class="eyebrow">
                        Evidence
                    </span>

                    <h3>
                        Cited documentation
                    </h3>

                </div>

                <span class="official-badge">
                    Official FastAPI docs
                </span>

            </div>

            <div class="source-grid">
                {sources_html}
            </div>

        </div>

    </article>
    """


# ============================================================
# CSS
# ============================================================

CSS = """
* {
    box-sizing: border-box;
}

:root {
    --background: #06111f;
    --background-two: #081727;

    --panel: #0d1b2d;
    --panel-two: #12243a;

    --border:
        rgba(148, 163, 184, 0.16);

    --text: #f8fafc;
    --muted: #94a3b8;

    --cyan: #22d3ee;
    --teal: #14b8a6;
    --blue: #3b82f6;
    --indigo: #6366f1;

    --green: #34d399;
    --danger: #fb7185;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;

    min-height: 100vh;

    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    color: var(--text);

    background:
        radial-gradient(
            circle at 15% 5%,
            rgba(34, 211, 238, 0.12),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(99, 102, 241, 0.11),
            transparent 30%
        ),
        linear-gradient(
            180deg,
            #06111f 0%,
            #071422 100%
        );

    line-height: 1.6;
}

body::before {
    content: "";

    position: fixed;
    inset: 0;

    pointer-events: none;

    background-image:
        linear-gradient(
            rgba(255,255,255,0.017) 1px,
            transparent 1px
        ),
        linear-gradient(
            90deg,
            rgba(255,255,255,0.017) 1px,
            transparent 1px
        );

    background-size:
        48px 48px;

    mask-image:
        linear-gradient(
            to bottom,
            rgba(0,0,0,.45),
            transparent 80%
        );
}

a {
    color: inherit;
}

button,
textarea,
select {
    font: inherit;
}

button {
    transition:
        transform .18s ease,
        border-color .18s ease,
        background .18s ease,
        color .18s ease;
}

.container {
    width:
        min(
            1180px,
            calc(100% - 36px)
        );

    margin:
        0 auto;
}


/* ==========================================================
   NAVIGATION
========================================================== */

nav {
    position: sticky;

    top: 0;

    z-index: 50;

    border-bottom:
        1px solid var(--border);

    background:
        rgba(6, 17, 31, 0.88);

    backdrop-filter:
        blur(18px);
}

.nav-inner {
    min-height: 72px;

    display: flex;

    align-items: center;

    justify-content:
        space-between;

    gap: 20px;
}

.brand {
    display: flex;

    align-items: center;

    gap: 11px;

    color: inherit;

    text-decoration: none;
}

.logo {
    width: 40px;
    height: 40px;

    display: grid;

    place-items: center;

    flex-shrink: 0;

    border-radius: 12px;

    color: #04141a;

    font-size: 13px;

    font-weight: 900;

    background:
        linear-gradient(
            135deg,
            var(--cyan),
            var(--teal)
        );

    box-shadow:
        0 0 30px
        rgba(34, 211, 238, .18);
}

.brand-text {
    display: flex;

    flex-direction: column;

    line-height: 1.25;
}

.brand-text strong {
    font-size: 14px;
}

.brand-text span {
    margin-top: 2px;

    color: var(--muted);

    font-size: 10px;
}

.nav-links {
    display: flex;

    gap: 5px;
}

.nav-links a {
    padding:
        8px 11px;

    border-radius: 9px;

    color: #cbd5e1;

    text-decoration: none;

    font-size: 12px;
}

.nav-links a:hover {
    color: #cffafe;

    background:
        rgba(34, 211, 238, .07);
}


/* ==========================================================
   HERO
========================================================== */

.hero {
    padding:
        72px 0 38px;
}

.hero-content {
    max-width: 850px;

    margin:
        0 auto;

    text-align: center;
}

.pill {
    display: inline-flex;

    padding:
        7px 12px;

    margin-bottom: 20px;

    border:
        1px solid
        rgba(34, 211, 238, .18);

    border-radius: 999px;

    color: #a5f3fc;

    background:
        rgba(34, 211, 238, .06);

    font-size: 11px;

    font-weight: 700;
}

.hero h1 {
    margin:
        0 0 18px;

    font-size:
        clamp(
            38px,
            7vw,
            68px
        );

    line-height: 1.05;

    letter-spacing: -.05em;
}

.gradient {
    color: transparent;

    background:
        linear-gradient(
            90deg,
            #67e8f9,
            #5eead4,
            #818cf8
        );

    background-clip: text;

    -webkit-background-clip: text;
}

.hero-description {
    max-width: 700px;

    margin:
        0 auto 35px;

    color: #cbd5e1;

    font-size: 17px;
}


/* ==========================================================
   SEARCH
========================================================== */

.search-panel {
    max-width: 920px;

    margin:
        0 auto;

    padding: 7px;

    border-radius: 23px;

    background:
        linear-gradient(
            135deg,
            rgba(34, 211, 238, .18),
            rgba(99, 102, 241, .11)
        );

    box-shadow:
        0 30px 80px
        rgba(0,0,0,.24);
}

.search-inner {
    padding: 24px;

    border:
        1px solid
        rgba(255,255,255,.06);

    border-radius: 18px;

    background:
        rgba(10,23,39,.98);
}

.search-row {
    display: flex;

    justify-content:
        space-between;

    align-items: center;

    gap: 14px;

    margin-bottom: 14px;
}

.search-label {
    color: #cbd5e1;

    font-size: 13px;

    font-weight: 700;
}

select {
    min-width: 220px;

    padding:
        10px 12px;

    border:
        1px solid var(--border);

    border-radius: 10px;

    outline: none;

    cursor: pointer;

    color: #e2e8f0;

    background:
        var(--panel-two);
}

select:focus {
    border-color:
        rgba(34,211,238,.5);
}

textarea {
    width: 100%;

    min-height: 145px;

    resize: vertical;

    padding: 17px;

    border:
        1px solid var(--border);

    border-radius: 15px;

    outline: none;

    color: white;

    background:
        rgba(255,255,255,.025);

    font-size: 15px;

    line-height: 1.6;
}

textarea:focus {
    border-color:
        rgba(34,211,238,.5);

    box-shadow:
        0 0 0 4px
        rgba(34,211,238,.05);
}

textarea::placeholder {
    color: #64748b;
}

.form-actions {
    display: flex;

    justify-content:
        space-between;

    align-items: center;

    gap: 12px;

    margin-top: 14px;
}

.button-group {
    display: flex;

    gap: 8px;
}

.primary-button {
    border: none;

    padding:
        12px 19px;

    border-radius: 11px;

    cursor: pointer;

    color: #04151c;

    font-weight: 800;

    background:
        linear-gradient(
            135deg,
            var(--cyan),
            var(--teal)
        );

    box-shadow:
        0 12px 30px
        rgba(20,184,166,.18);
}

.primary-button:hover {
    transform:
        translateY(-1px);

    filter:
        brightness(1.06);
}

.outline-button {
    padding:
        9px 12px;

    cursor: pointer;

    border:
        1px solid var(--border);

    border-radius: 9px;

    color: #cbd5e1;

    background:
        rgba(255,255,255,.025);
}

.outline-button:hover {
    color: #cffafe;

    border-color:
        rgba(34,211,238,.35);

    background:
        rgba(34,211,238,.05);
}

.hint {
    color: var(--muted);

    font-size: 11px;
}


/* ==========================================================
   EXAMPLES + HISTORY
========================================================== */

.example-area {
    margin-top: 17px;
}

.small-title {
    margin-bottom: 9px;

    color: var(--muted);

    font-size: 11px;
}

.chips {
    display: flex;

    flex-wrap: wrap;

    gap: 7px;
}

.chip {
    border:
        1px solid var(--border);

    border-radius: 999px;

    padding:
        7px 11px;

    cursor: pointer;

    color: #cbd5e1;

    background:
        rgba(255,255,255,.02);

    font-size: 11px;
}

.chip:hover {
    color: #cffafe;

    border-color:
        rgba(34,211,238,.3);

    background:
        rgba(34,211,238,.05);
}

.history-area {
    max-width: 920px;

    margin:
        18px auto 0;

    padding: 15px;

    border:
        1px solid var(--border);

    border-radius: 14px;

    background:
        rgba(255,255,255,.018);
}

.history-header {
    display: flex;

    justify-content:
        space-between;

    align-items: center;

    gap: 10px;

    margin-bottom: 9px;
}

.history-header strong {
    font-size: 12px;
}

.history-empty {
    color: var(--muted);

    font-size: 11px;
}


/* ==========================================================
   RESULT AREA
========================================================== */

.results-section {
    padding:
        35px 0 80px;
}

.section-header {
    display: flex;

    justify-content:
        space-between;

    align-items:
        flex-end;

    gap: 16px;

    margin-bottom: 16px;
}

.eyebrow {
    display: block;

    margin-bottom: 4px;

    color: #67e8f9;

    font-size: 9px;

    font-weight: 800;

    text-transform: uppercase;

    letter-spacing: .14em;
}

.section-header h2,
.answer-heading h2 {
    margin: 0;

    font-size: 22px;

    letter-spacing: -.025em;
}

.compare-layout {
    display: grid;

    grid-template-columns:
        repeat(
            2,
            minmax(0,1fr)
        );

    gap: 16px;
}


/* ==========================================================
   ANSWER CARD
========================================================== */

.answer-card {
    overflow: hidden;

    margin-bottom: 18px;

    border:
        1px solid var(--border);

    border-radius: 18px;

    background:
        rgba(13,27,45,.95);

    box-shadow:
        0 20px 60px
        rgba(0,0,0,.22);
}

.answer-heading {
    padding: 17px;

    display: flex;

    align-items: center;

    justify-content:
        space-between;

    gap: 10px;

    border-bottom:
        1px solid var(--border);
}

.answer-card.compact
.answer-heading h2 {
    font-size: 17px;
}

.stats {
    display: grid;

    grid-template-columns:
        repeat(3,1fr);

    gap: 1px;

    background:
        var(--border);
}

.stat {
    padding:
        11px 13px;

    background:
        #0c1a2b;
}

.stat span {
    display: block;

    color: var(--muted);

    font-size: 9px;
}

.stat strong {
    color: #e2e8f0;

    font-size: 12px;
}

.answer-content {
    padding: 22px;

    color: #dbeafe;

    font-size: 14px;

    line-height: 1.78;
}

.answer-content p {
    margin:
        0 0 14px;
}

.answer-subheading {
    margin:
        22px 0 8px;

    color: #f1f5f9;

    font-size: 15px;
}

.answer-list {
    margin:
        5px 0 16px;

    padding-left: 22px;
}

.answer-list li {
    margin-bottom: 7px;
}

.answer-content code {
    padding:
        2px 5px;

    border:
        1px solid
        rgba(34,211,238,.1);

    border-radius: 5px;

    color: #a5f3fc;

    background:
        rgba(34,211,238,.07);
}

.citation {
    display: inline-block;

    margin:
        0 2px;

    padding:
        1px 6px;

    border:
        1px solid
        rgba(34,211,238,.14);

    border-radius: 999px;

    color: #67e8f9;

    background:
        rgba(34,211,238,.07);

    font-size: 10px;

    font-weight: 700;
}


/* ==========================================================
   CODE BLOCK
========================================================== */

.code-wrapper {
    overflow: hidden;

    margin:
        18px 0;

    border:
        1px solid var(--border);

    border-radius: 11px;

    background: #040b14;
}

.code-header {
    padding:
        8px 11px;

    display: flex;

    justify-content:
        space-between;

    align-items: center;

    border-bottom:
        1px solid var(--border);

    color: var(--muted);

    font-size: 10px;
}

.code-header button {
    border:
        1px solid var(--border);

    border-radius: 7px;

    padding:
        4px 8px;

    cursor: pointer;

    color: #cbd5e1;

    background: transparent;
}

pre {
    overflow: auto;

    margin: 0;

    padding: 15px;
}

pre code {
    padding: 0 !important;

    border: 0 !important;

    color: #d1fae5 !important;

    background:
        transparent !important;

    font-size: 12px;

    line-height: 1.65;
}


/* ==========================================================
   SOURCES
========================================================== */

.sources-block {
    padding:
        0 18px 19px;
}

.sources-heading {
    display: flex;

    align-items:
        flex-end;

    justify-content:
        space-between;

    gap: 12px;

    margin-bottom: 11px;
}

.sources-heading h3 {
    margin: 0;

    font-size: 13px;
}

.official-badge {
    padding:
        5px 9px;

    border:
        1px solid
        rgba(52,211,153,.15);

    border-radius: 999px;

    color: #a7f3d0;

    background:
        rgba(52,211,153,.05);

    font-size: 9px;
}

.source-grid {
    display: grid;

    grid-template-columns:
        repeat(
            2,
            minmax(0,1fr)
        );

    gap: 9px;
}

.compact
.source-grid {
    grid-template-columns:
        1fr;
}

.source-card {
    min-width: 0;

    display: block;

    padding: 13px;

    border:
        1px solid var(--border);

    border-radius: 11px;

    color: inherit;

    text-decoration: none;

    background:
        rgba(255,255,255,.018);
}

.source-card:hover {
    border-color:
        rgba(34,211,238,.3);

    background:
        rgba(34,211,238,.03);
}

.source-top {
    display: flex;

    justify-content:
        space-between;

    gap: 8px;

    margin-bottom: 9px;
}

.source-number {
    width: 23px;
    height: 23px;

    display: grid;

    place-items: center;

    border-radius: 7px;

    color: #67e8f9;

    background:
        rgba(34,211,238,.07);

    font-size: 10px;

    font-weight: 800;
}

.source-score {
    color: var(--muted);

    font-size: 9px;
}

.source-card strong {
    display: block;

    margin-bottom: 4px;

    font-size: 12px;
}

.source-card small {
    display: block;

    overflow: hidden;

    color: #64748b;

    font-size: 9px;

    white-space: nowrap;

    text-overflow: ellipsis;
}

.source-link {
    display: block;

    margin-top: 9px;

    color: #67e8f9;

    font-size: 10px;
}

.empty-card {
    padding: 14px;

    border:
        1px dashed var(--border);

    border-radius: 10px;

    color: var(--muted);

    font-size: 11px;
}


/* ==========================================================
   ABOUT + RESULTS PAGES
========================================================== */

.page-content {
    padding:
        58px 0 80px;
}

.page-heading {
    max-width: 760px;

    margin-bottom: 32px;
}

.page-heading h1 {
    margin:
        0 0 12px;

    font-size:
        clamp(
            34px,
            6vw,
            54px
        );

    letter-spacing: -.04em;
}

.page-heading p {
    color: #cbd5e1;
}

.info-grid {
    display: grid;

    grid-template-columns:
        repeat(
            2,
            minmax(0,1fr)
        );

    gap: 14px;
}

.info-card {
    padding: 20px;

    border:
        1px solid var(--border);

    border-radius: 15px;

    background:
        rgba(255,255,255,.02);
}

.info-card h2 {
    margin:
        0 0 8px;

    font-size: 16px;
}

.info-card p {
    margin: 0;

    color: #cbd5e1;

    font-size: 13px;
}

.metric-grid {
    display: grid;

    grid-template-columns:
        repeat(
            4,
            minmax(0,1fr)
        );

    gap: 11px;

    margin-bottom: 28px;
}

.metric-card {
    padding: 16px;

    border:
        1px solid var(--border);

    border-radius: 13px;

    background:
        rgba(255,255,255,.02);
}

.metric-card span {
    display: block;

    color: var(--muted);

    font-size: 10px;
}

.metric-card strong {
    display: block;

    margin-top: 4px;

    color: #e2e8f0;

    font-size: 20px;
}

.graph-section {
    margin-top: 36px;
}

.graph-section h2 {
    margin-top: 0;
}

.graph-grid {
    display: grid;

    grid-template-columns:
        repeat(
            2,
            minmax(0,1fr)
        );

    gap: 16px;

    margin-top: 15px;
}

.graph-card {
    padding: 10px;

    border:
        1px solid var(--border);

    border-radius: 14px;

    background: white;
}

.graph-card img {
    display: block;

    width: 100%;

    border-radius: 8px;
}


/* ==========================================================
   ERRORS
========================================================== */

.error-card {
    max-width: 900px;

    margin:
        0 auto;

    padding: 18px;

    border:
        1px solid
        rgba(251,113,133,.25);

    border-radius: 13px;

    color: #fecdd3;

    background:
        rgba(251,113,133,.06);
}

.error-card strong {
    display: block;

    margin-bottom: 5px;
}


/* ==========================================================
   LOADING
========================================================== */

.loading-overlay {
    display: none;

    position: fixed;

    inset: 0;

    z-index: 999;

    place-items: center;

    background:
        rgba(2,8,18,.84);

    backdrop-filter:
        blur(12px);
}

.loading-overlay.active {
    display: grid;
}

.loading-box {
    width:
        min(
            360px,
            calc(100% - 36px)
        );

    padding: 28px;

    text-align: center;

    border:
        1px solid var(--border);

    border-radius: 18px;

    background:
        var(--panel);

    box-shadow:
        0 30px 80px
        rgba(0,0,0,.35);
}

.loader {
    width: 42px;
    height: 42px;

    margin:
        0 auto 17px;

    border:
        3px solid
        rgba(255,255,255,.08);

    border-top-color:
        var(--cyan);

    border-radius: 50%;

    animation:
        spin .8s linear infinite;
}

@keyframes spin {
    to {
        transform:
            rotate(360deg);
    }
}

.loading-box p {
    margin-bottom: 0;

    color: var(--muted);

    font-size: 11px;
}


/* ==========================================================
   FOOTER
========================================================== */

footer {
    padding:
        25px 0;

    border-top:
        1px solid var(--border);

    color: #64748b;

    font-size: 10px;
}


/* ==========================================================
   RESPONSIVE
========================================================== */

@media (
    max-width: 850px
) {

    .compare-layout,
    .info-grid,
    .graph-grid {
        grid-template-columns:
            1fr;
    }

    .metric-grid {
        grid-template-columns:
            repeat(2,1fr);
    }

    .source-grid {
        grid-template-columns:
            1fr;
    }

}

@media (
    max-width: 650px
) {

    .nav-inner {
        flex-direction: column;

        align-items: stretch;

        padding:
            10px 0;
    }

    .nav-links {
        justify-content:
            space-between;
    }

    .nav-links a {
        flex: 1;

        text-align: center;
    }

    .hero {
        padding-top: 48px;
    }

    .search-row,
    .form-actions,
    .section-header,
    .answer-heading,
    .sources-heading {
        align-items: stretch;

        flex-direction: column;
    }

    select {
        width: 100%;

        min-width: 0;
    }

    .button-group {
        width: 100%;
    }

    .button-group button {
        flex: 1;
    }

    .stats {
        grid-template-columns:
            1fr;
    }

    .metric-grid {
        grid-template-columns:
            1fr;
    }

    .official-badge {
        width: fit-content;
    }

}
"""


# ============================================================
# JAVASCRIPT
# ============================================================

JS = """
const form =
    document.getElementById(
        "question-form"
    );

const questionInput =
    document.getElementById(
        "question-input"
    );

const loadingOverlay =
    document.getElementById(
        "loading-overlay"
    );

const historyContainer =
    document.getElementById(
        "history-container"
    );

const HISTORY_KEY =
    "fastapi_assistant_history";


function getHistory() {

    try {

        return JSON.parse(
            sessionStorage.getItem(
                HISTORY_KEY
            ) || "[]"
        );

    } catch (error) {

        return [];

    }

}


function saveQuestion(question) {

    if (!question) {
        return;
    }

    let history =
        getHistory();

    history =
        history.filter(
            item =>
                item !== question
        );

    history.unshift(
        question
    );

    history =
        history.slice(
            0,
            8
        );

    sessionStorage.setItem(
        HISTORY_KEY,
        JSON.stringify(
            history
        )
    );

}


function renderHistory() {

    if (!historyContainer) {
        return;
    }

    const history =
        getHistory();

    historyContainer.innerHTML =
        "";

    if (
        history.length === 0
    ) {

        historyContainer.innerHTML =
            '<div class="history-empty">' +
            'No questions in this session yet.' +
            '</div>';

        return;

    }

    const wrapper =
        document.createElement(
            "div"
        );

    wrapper.className =
        "chips";

    history.forEach(
        question => {

            const button =
                document.createElement(
                    "button"
                );

            button.type =
                "button";

            button.className =
                "chip";

            button.textContent =
                question.length > 58
                ? question.slice(
                    0,
                    58
                ) + "..."
                : question;

            button.title =
                question;

            button.addEventListener(
                "click",
                () => {

                    if (
                        questionInput
                    ) {

                        questionInput.value =
                            question;

                        questionInput.focus();

                        window.scrollTo({
                            top: 0,
                            behavior: "smooth"
                        });

                    }

                }
            );

            wrapper.appendChild(
                button
            );

        }
    );

    historyContainer.appendChild(
        wrapper
    );

}


function clearHistory() {

    sessionStorage.removeItem(
        HISTORY_KEY
    );

    renderHistory();

}


function clearQuestion() {

    if (!questionInput) {
        return;
    }

    questionInput.value =
        "";

    questionInput.focus();

}


if (form) {

    form.addEventListener(
        "submit",
        () => {

            const question =
                questionInput
                    .value
                    .trim();

            saveQuestion(
                question
            );

            if (
                loadingOverlay
            ) {

                loadingOverlay
                    .classList
                    .add(
                        "active"
                    );

            }

        }
    );

}


document
    .querySelectorAll(
        ".example-chip"
    )
    .forEach(
        button => {

            button.addEventListener(
                "click",
                () => {

                    if (
                        questionInput
                    ) {

                        questionInput.value =
                            button.dataset
                                .question;

                        questionInput
                            .focus();

                    }

                }
            );

        }
    );


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

        if (button) {

            const original =
                button.innerText;

            button.innerText =
                "Copied";

            setTimeout(
                () => {

                    button.innerText =
                        original;

                },
                1200
            );

        }

    } catch (error) {

        console.error(
            "Could not copy answer.",
            error
        );

    }

}


async function copyCode(
    button
) {

    const wrapper =
        button.closest(
            ".code-wrapper"
        );

    if (!wrapper) {
        return;
    }

    const code =
        wrapper.querySelector(
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
            1200
        );

    } catch (error) {

        console.error(
            "Could not copy code.",
            error
        );

    }

}


renderHistory();
"""


# ============================================================
# SHARED NAVIGATION
# ============================================================

def nav_html():
    return """
    <nav>

        <div class="container nav-inner">

            <a
                href="/"
                class="brand"
            >

                <div class="logo">
                    FA
                </div>

                <div class="brand-text">

                    <strong>
                        FastAPI Docs Assistant
                    </strong>

                    <span>
                        RAG documentation search
                    </span>

                </div>

            </a>


            <div class="nav-links">

                <a href="/">
                    Assistant
                </a>

                <a href="/about">
                    About
                </a>

                <a href="/results">
                    Results
                </a>

            </div>

        </div>

    </nav>
    """


# ============================================================
# SHARED HTML DOCUMENT
# ============================================================

def document(
    content,
    title=APP_TITLE,
    include_js=False,
):
    script_html = ""

    if include_js:
        script_html = (
            f"<script>{JS}</script>"
        )

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
                initial-scale=1
            "
        >

        <title>
            {safe_title}
        </title>

        <style>
            {CSS}
        </style>

    </head>


    <body>

        {nav_html()}

        {content}

        <footer>

            <div class="container">

                RAG-Based Technical
                Documentation Assistant
                · Official FastAPI
                documentation corpus

            </div>

        </footer>

        {script_html}

    </body>

    </html>
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

    result_html = ""

    if error:
        safe_error = html.escape(
            error
        )

        result_html = f"""
        <section class="results-section">

            <div class="container">

                <div class="error-card">

                    <strong>
                        Unable to generate answer
                    </strong>

                    <div>
                        {safe_error}
                    </div>

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

        result_html = f"""
        <section
            class="results-section"
            id="results"
        >

            <div class="container">

                <div class="section-header">

                    <div>

                        <span class="eyebrow">
                            Compare mode
                        </span>

                        <h2>
                            Semantic vs BM25
                        </h2>

                    </div>

                    <span class="hint">
                        Same question · same corpus ·
                        same language model
                    </span>

                </div>


                <div class="compare-layout">

                    {semantic_card}

                    {bm25_card}

                </div>

            </div>

        </section>
        """

    elif result:
        card = result_card(
            result,
            "main-answer",
        )

        result_html = f"""
        <section
            class="results-section"
            id="results"
        >

            <div class="container">

                {card}

            </div>

        </section>
        """

    safe_question = html.escape(
        question,
        quote=True,
    )

    content = f"""
    <div
        id="loading-overlay"
        class="loading-overlay"
    >

        <div class="loading-box">

            <div class="loader"></div>

            <strong>
                Searching FastAPI documentation...
            </strong>

            <p>
                Retrieving relevant context
                and generating a grounded answer.
            </p>

        </div>

    </div>


    <main>

        <section class="hero">

            <div class="container">

                <div class="hero-content">

                    <div class="pill">
                        Retrieval-Augmented Generation
                    </div>

                    <h1>

                        Ask FastAPI.

                        <span class="gradient">
                            Get grounded answers.
                        </span>

                    </h1>

                    <p class="hero-description">

                        Search official FastAPI
                        documentation using semantic
                        vector retrieval, BM25 keyword
                        search, or compare both
                        approaches side by side.

                    </p>

                </div>


                <form
                    method="post"
                    action="/"
                    id="question-form"
                    class="search-panel"
                >

                    <div class="search-inner">

                        <div class="search-row">

                            <div class="search-label">
                                Ask a FastAPI question
                            </div>


                            <select
                                name="retrieval_method"
                                aria-label="
                                    Retrieval method
                                "
                            >

                                <option
                                    value="semantic"
                                    {semantic_selected}
                                >
                                    Semantic / Vector
                                </option>

                                <option
                                    value="bm25"
                                    {bm25_selected}
                                >
                                    BM25 Keyword
                                </option>

                                <option
                                    value="compare"
                                    {compare_selected}
                                >
                                    Compare Both
                                </option>

                            </select>

                        </div>


                        <textarea
                            name="question"
                            id="question-input"
                            required
                            placeholder="How do I handle request validation errors in FastAPI?"
                        >{safe_question}</textarea>


                        <div class="form-actions">

                            <span class="hint">

                                Answers are grounded
                                in retrieved official
                                FastAPI documentation.

                            </span>


                            <div class="button-group">

                                <button
                                    type="button"
                                    class="outline-button"
                                    onclick="
                                        clearQuestion()
                                    "
                                >
                                    Clear
                                </button>

                                <button
                                    type="submit"
                                    class="primary-button"
                                >
                                    Ask documentation
                                </button>

                            </div>

                        </div>


                        <div class="example-area">

                            <div class="small-title">
                                Try an example
                            </div>


                            <div class="chips">

                                <button
                                    type="button"
                                    class="
                                        chip
                                        example-chip
                                    "
                                    data-question="How do I handle request validation errors in FastAPI?"
                                >
                                    Validation errors
                                </button>

                                <button
                                    type="button"
                                    class="
                                        chip
                                        example-chip
                                    "
                                    data-question="How do I use dependency injection in FastAPI?"
                                >
                                    Dependencies
                                </button>

                                <button
                                    type="button"
                                    class="
                                        chip
                                        example-chip
                                    "
                                    data-question="How do I upload files in FastAPI?"
                                >
                                    File uploads
                                </button>

                                <button
                                    type="button"
                                    class="
                                        chip
                                        example-chip
                                    "
                                    data-question="How do I create a WebSocket endpoint in FastAPI?"
                                >
                                    WebSockets
                                </button>

                                <button
                                    type="button"
                                    class="
                                        chip
                                        example-chip
                                    "
                                    data-question="How do I configure CORS in FastAPI?"
                                >
                                    CORS
                                </button>

                            </div>

                        </div>

                    </div>

                </form>


                <div class="history-area">

                    <div class="history-header">

                        <strong>
                            Session history
                        </strong>

                        <button
                            type="button"
                            class="outline-button"
                            onclick="
                                clearHistory()
                            "
                        >
                            Clear history
                        </button>

                    </div>

                    <div
                        id="history-container"
                    ></div>

                </div>

            </div>

        </section>

        {result_html}

    </main>
    """

    return document(
        content,
        include_js=True,
    )


# ============================================================
# ABOUT PAGE
# ============================================================

def about_page():
    content = """
    <main class="page-content">

        <div class="container">

            <div class="page-heading">

                <span class="eyebrow">
                    Project methodology
                </span>

                <h1>
                    How the assistant works
                </h1>

                <p>
                    This project investigates how
                    retrieval-augmented generation
                    can support technical
                    documentation question answering
                    using official FastAPI
                    documentation.
                </p>

            </div>


            <div class="info-grid">

                <article class="info-card">

                    <h2>
                        1. Documentation corpus
                    </h2>

                    <p>
                        Official English FastAPI
                        documentation pages are
                        collected and processed into
                        smaller chunks while
                        preserving their titles,
                        headings and source URLs.
                    </p>

                </article>


                <article class="info-card">

                    <h2>
                        2. Semantic retrieval
                    </h2>

                    <p>
                        Documentation chunks are
                        represented using pretrained
                        sentence embeddings.
                        Questions are embedded using
                        the same model and chunks are
                        ranked according to semantic
                        similarity.
                    </p>

                </article>


                <article class="info-card">

                    <h2>
                        3. BM25 retrieval
                    </h2>

                    <p>
                        BM25 acts as the keyword-based
                        baseline. It ranks the same
                        documentation corpus using
                        lexical term matching, allowing
                        a direct comparison with
                        semantic retrieval.
                    </p>

                </article>


                <article class="info-card">

                    <h2>
                        4. Grounded generation
                    </h2>

                    <p>
                        The highest-ranked
                        documentation chunks are
                        supplied to a pretrained
                        language model. The model is
                        instructed to answer using only
                        the retrieved context and to
                        cite its documentation
                        sources.
                    </p>

                </article>


                <article class="info-card">

                    <h2>
                        5. Evaluation
                    </h2>

                    <p>
                        The project evaluates retrieval
                        accuracy, ranking quality,
                        answer correctness, source
                        support, unsupported claims,
                        response time and failure
                        cases.
                    </p>

                </article>


                <article class="info-card">

                    <h2>
                        6. Compare mode
                    </h2>

                    <p>
                        A single question can be
                        processed independently with
                        semantic retrieval and BM25.
                        Their generated answers,
                        sources and response times can
                        then be inspected side by
                        side.
                    </p>

                </article>

            </div>

        </div>

    </main>
    """

    return document(
        content,
        title=(
            "About · "
            + APP_TITLE
        ),
    )


# ============================================================
# LOAD EVALUATION RESULTS
# ============================================================

def load_results():
    if not RESULTS_FILE.exists():
        return None

    try:
        with RESULTS_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except Exception as exc:
        print(
            "Could not load results:",
            repr(exc),
        )

        return None


# ============================================================
# RESULTS PAGE
# ============================================================

def results_page():
    data = load_results()

    if not data:
        content = """
        <main class="page-content">

            <div class="container">

                <div class="error-card">

                    <strong>
                        Evaluation results unavailable
                    </strong>

                    The evaluation summary could not
                    be loaded.

                </div>

            </div>

        </main>
        """

        return document(
            content,
            title=(
                "Results · "
                + APP_TITLE
            ),
        )

    semantic_retrieval = (
        data[
            "retrieval_results"
        ]["semantic"]
    )

    bm25_retrieval = (
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

    # --------------------------------------------------------
    # PRE-FORMAT METRICS
    # --------------------------------------------------------

    semantic_top1 = (
        f'{semantic_retrieval["hit_at_1"] * 100:.0f}%'
    )

    semantic_top3 = (
        f'{semantic_retrieval["hit_at_3"] * 100:.0f}%'
    )

    semantic_top5 = (
        f'{semantic_retrieval["hit_at_5"] * 100:.0f}%'
    )

    bm25_top1 = (
        f'{bm25_retrieval["hit_at_1"] * 100:.0f}%'
    )

    bm25_top3 = (
        f'{bm25_retrieval["hit_at_3"] * 100:.0f}%'
    )

    bm25_top5 = (
        f'{bm25_retrieval["hit_at_5"] * 100:.0f}%'
    )

    semantic_mrr = (
        f'{semantic_retrieval["mean_reciprocal_rank"]:.3f}'
    )

    bm25_mrr = (
        f'{bm25_retrieval["mean_reciprocal_rank"]:.3f}'
    )

    semantic_correctness = (
        f'{semantic_answer["correctness_percentage"]:.1f}%'
    )

    bm25_correctness = (
        f'{bm25_answer["correctness_percentage"]:.1f}%'
    )

    semantic_support = (
        f'{semantic_answer["average_source_support_score"]:.1f}'
    )

    bm25_support = (
        f'{bm25_answer["average_source_support_score"]:.1f}'
    )

    semantic_unsupported = (
        semantic_answer[
            "total_unsupported_claims"
        ]
    )

    bm25_unsupported = (
        bm25_answer[
            "total_unsupported_claims"
        ]
    )

    semantic_retrieval_time = (
        f'{semantic_retrieval["average_response_time_ms"]:.2f} ms'
    )

    bm25_retrieval_time = (
        f'{bm25_retrieval["average_response_time_ms"]:.2f} ms'
    )

    semantic_total_time = (
        f'{semantic_answer["average_total_response_time_ms"] / 1000:.2f} s'
    )

    bm25_total_time = (
        f'{bm25_answer["average_total_response_time_ms"] / 1000:.2f} s'
    )

    # --------------------------------------------------------
    # GRAPHS
    # --------------------------------------------------------

    graph_names = [
        (
            "retrieval_accuracy.png",
            "Retrieval Accuracy",
        ),
        (
            "mean_reciprocal_rank.png",
            "Mean Reciprocal Rank",
        ),
        (
            "answer_correctness.png",
            "Answer Correctness",
        ),
        (
            "retrieval_response_time.png",
            "Retrieval Response Time",
        ),
        (
            "total_response_time.png",
            "End-to-End Response Time",
        ),
    ]

    graph_cards = []

    for filename, label in graph_names:
        path = (
            GRAPHS_DIR
            / filename
        )

        if path.exists():
            graph_cards.append(
                f"""
                <article class="graph-card">

                    <img
                        src="/graphs/{filename}"
                        alt="{html.escape(label)}"
                    >

                </article>
                """
            )

    graphs_html = "\n".join(
        graph_cards
    )

    graphs_section = ""

    if graphs_html:
        graphs_section = f"""
        <section class="graph-section">

            <span class="eyebrow">
                Visual analysis
            </span>

            <h2>
                Evaluation graphs
            </h2>

            <div class="graph-grid">
                {graphs_html}
            </div>

        </section>
        """

    # --------------------------------------------------------
    # RESULTS HTML
    # --------------------------------------------------------

    content = f"""
    <main class="page-content">

        <div class="container">

            <div class="page-heading">

                <span class="eyebrow">
                    Candidate evaluation
                </span>

                <h1>
                    Evaluation results
                </h1>

                <p>
                    These results compare semantic
                    retrieval with BM25 using the
                    current 20-question candidate
                    evaluation set.
                </p>

            </div>


            <div class="metric-grid">

                <div class="metric-card">

                    <span>
                        Semantic Top-1
                    </span>

                    <strong>
                        {semantic_top1}
                    </strong>

                </div>


                <div class="metric-card">

                    <span>
                        BM25 Top-1
                    </span>

                    <strong>
                        {bm25_top1}
                    </strong>

                </div>


                <div class="metric-card">

                    <span>
                        Semantic Top-3
                    </span>

                    <strong>
                        {semantic_top3}
                    </strong>

                </div>


                <div class="metric-card">

                    <span>
                        BM25 Top-3
                    </span>

                    <strong>
                        {bm25_top3}
                    </strong>

                </div>


                <div class="metric-card">

                    <span>
                        Semantic Top-5
                    </span>

                    <strong>
                        {semantic_top5}
                    </strong>

                </div>


                <div class="metric-card">

                    <span>
                        BM25 Top-5
                    </span>

                    <strong>
                        {bm25_top5}
                    </strong>

                </div>


                <div class="metric-card">

                    <span>
                        Semantic MRR
                    </span>

                    <strong>
                        {semantic_mrr}
                    </strong>

                </div>


                <div class="metric-card">

                    <span>
                        BM25 MRR
                    </span>

                    <strong>
                        {bm25_mrr}
                    </strong>

                </div>


                <div class="metric-card">

                    <span>
                        Semantic answer correctness
                    </span>

                    <strong>
                        {semantic_correctness}
                    </strong>

                </div>


                <div class="metric-card">

                    <span>
                        BM25 answer correctness
                    </span>

                    <strong>
                        {bm25_correctness}
                    </strong>

                </div>


                <div class="metric-card">

                    <span>
                        Semantic retrieval time
                    </span>

                    <strong>
                        {semantic_retrieval_time}
                    </strong>

                </div>


                <div class="metric-card">

                    <span>
                        BM25 retrieval time
                    </span>

                    <strong>
                        {bm25_retrieval_time}
                    </strong>

                </div>

            </div>


            <div class="info-grid">

                <article class="info-card">

                    <h2>
                        Answer source support
                    </h2>

                    <p>
                        Semantic retrieval achieved
                        {semantic_support} / 3 average
                        source support. BM25 achieved
                        {bm25_support} / 3.
                    </p>

                </article>


                <article class="info-card">

                    <h2>
                        Unsupported claims
                    </h2>

                    <p>
                        Semantic answers contained
                        {semantic_unsupported}
                        unsupported claims and BM25
                        answers contained
                        {bm25_unsupported}.
                    </p>

                </article>


                <article class="info-card">

                    <h2>
                        End-to-end response time
                    </h2>

                    <p>
                        Semantic responses averaged
                        {semantic_total_time}.
                        BM25 responses averaged
                        {bm25_total_time}.
                    </p>

                </article>


                <article class="info-card">

                    <h2>
                        Current interpretation
                    </h2>

                    <p>
                        Semantic retrieval performed
                        better on retrieval quality
                        and answer correctness in the
                        current candidate evaluation,
                        while BM25 produced a lower
                        average end-to-end response
                        time.
                    </p>

                </article>

            </div>

            {graphs_section}

        </div>

    </main>
    """

    return document(
        content,
        title=(
            "Results · "
            + APP_TITLE
        ),
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
    question: str = Form(...),
    retrieval_method: str = Form(
        "semantic"
    ),
):
    question = question.strip()

    if not question:
        return home_page(
            error=(
                "Please enter a question."
            )
        )

    valid_methods = {
        "semantic",
        "bm25",
        "compare",
    }

    if (
        retrieval_method
        not in valid_methods
    ):
        retrieval_method = (
            "semantic"
        )

    try:
        # ----------------------------------------------------
        # COMPARE BOTH
        # ----------------------------------------------------

        if (
            retrieval_method
            == "compare"
        ):
            semantic_result = (
                run_rag(
                    question,
                    "semantic",
                )
            )

            bm25_result = (
                run_rag(
                    question,
                    "bm25",
                )
            )

            return home_page(
                question=question,
                method="compare",
                compare_results=[
                    semantic_result,
                    bm25_result,
                ],
            )

        # ----------------------------------------------------
        # SINGLE METHOD
        # ----------------------------------------------------

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
        # Full technical error is printed
        # only in the terminal.
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
    allowed_files = {
        "retrieval_accuracy.png",
        "mean_reciprocal_rank.png",
        "answer_correctness.png",
        "retrieval_response_time.png",
        "total_response_time.png",
    }

    if (
        filename
        not in allowed_files
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                "Graph not found."
            ),
        )

    path = (
        GRAPHS_DIR
        / filename
    )

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Graph not found."
            ),
        )

    return FileResponse(path)