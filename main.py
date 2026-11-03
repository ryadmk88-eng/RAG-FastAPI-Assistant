import html
import os
import re

from dotenv import load_dotenv
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from semantic_search import (
    load_data,
    semantic_search,
    MODEL_NAME,
)

from bm25_search import (
    build_bm25,
    bm25_search,
)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

load_dotenv()

app = FastAPI(
    title="RAG FastAPI Documentation Assistant"
)

LLM_MODEL = "gpt-6-luna"
TOP_K = 5

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)


# ---------------------------------------------------------
# Load shared corpus once
# ---------------------------------------------------------

print("Loading FastAPI corpus...")

chunks, embeddings = load_data()

print(f"Loaded {len(chunks)} chunks.")


# ---------------------------------------------------------
# Semantic retrieval setup
# ---------------------------------------------------------

print("Loading semantic embedding model...")

embedding_model = SentenceTransformer(
    MODEL_NAME
)


# ---------------------------------------------------------
# BM25 setup
# ---------------------------------------------------------

print("Building BM25 index...")

bm25_index = build_bm25(
    chunks
)

print("Retrieval systems ready.")


# ---------------------------------------------------------
# Source handling
# ---------------------------------------------------------

def build_source_map(results):
    source_map = {}

    for result in results:
        url = result["url"]

        if url not in source_map:
            source_map[url] = {
                "number": len(source_map) + 1,
                "title": result["title"],
                "url": url,
            }

    return source_map


def build_context(results, source_map):
    context_parts = []

    for result in results:
        source_number = (
            source_map[result["url"]]["number"]
        )

        context_parts.append(
            f"""
SOURCE {source_number}
Title: {result['title']}
Heading: {result['heading']}
URL: {result['url']}

Documentation:
{result['text']}
"""
        )

    return "\n".join(
        context_parts
    )


# ---------------------------------------------------------
# LLM generation
# ---------------------------------------------------------

def generate_answer(
    question,
    results,
    source_map
):
    context = build_context(
        results,
        source_map
    )

    valid_sources = ", ".join(
        f"[Source {source['number']}]"
        for source in source_map.values()
    )

    prompt = f"""
You are a technical documentation assistant for FastAPI.

Answer the user's question using ONLY the FastAPI documentation
provided below.

Rules:
- Do not invent information.
- If the documentation does not contain enough information, say so.
- Give a clear and concise technical answer.
- Cite supporting evidence using [Source 1], [Source 2], etc.
- Only use these valid citations: {valid_sources}
- Do not cite a source unless it supports the statement.
- Multiple excerpts with the same source number come from the same page.
- Do not use outside knowledge.

USER QUESTION:
{question}

FASTAPI DOCUMENTATION:
{context}
"""

    response = client.responses.create(
        model=LLM_MODEL,
        input=prompt,
    )

    return response.output_text


# ---------------------------------------------------------
# Find sources actually cited by LLM
# ---------------------------------------------------------

def extract_cited_source_numbers(answer):
    matches = re.findall(
        r"\[Source (\d+)\]",
        answer
    )

    return {
        int(number)
        for number in matches
    }


# ---------------------------------------------------------
# Format generated answer for HTML
# ---------------------------------------------------------

def format_answer(answer):
    safe_answer = html.escape(
        answer
    )

    code_blocks = []

    def replace_code_block(match):
        code = match.group(1).strip()

        placeholder = (
            f"CODEBLOCKPLACEHOLDER"
            f"{len(code_blocks)}"
        )

        code_blocks.append(
            f"<pre><code>{code}</code></pre>"
        )

        return placeholder

    safe_answer = re.sub(
        r"```(?:python)?\s*(.*?)```",
        replace_code_block,
        safe_answer,
        flags=re.DOTALL | re.IGNORECASE,
    )

    safe_answer = re.sub(
        r"`([^`\n]+)`",
        r"<code>\1</code>",
        safe_answer,
    )

    safe_answer = re.sub(
        r"\[Source (\d+)\]",
        (
            r'<span class="citation">'
            r'[Source \1]'
            r'</span>'
        ),
        safe_answer,
    )

    blocks = re.split(
        r"\n\s*\n",
        safe_answer
    )

    formatted_blocks = []

    for block in blocks:
        block = block.strip()

        if not block:
            continue

        if block.startswith(
            "CODEBLOCKPLACEHOLDER"
        ):
            formatted_blocks.append(
                block
            )

        else:
            formatted_blocks.append(
                "<p>"
                + block.replace(
                    "\n",
                    "<br>"
                )
                + "</p>"
            )

    formatted = "\n".join(
        formatted_blocks
    )

    for index, code_html in enumerate(
        code_blocks
    ):
        formatted = formatted.replace(
            f"CODEBLOCKPLACEHOLDER{index}",
            code_html,
        )

    return formatted


# ---------------------------------------------------------
# Source list
# ---------------------------------------------------------

def build_source_html(
    source_map,
    cited_numbers
):
    source_items = []

    for source in source_map.values():

        if (
            source["number"]
            not in cited_numbers
        ):
            continue

        title = html.escape(
            source["title"]
        )

        url = html.escape(
            source["url"],
            quote=True
        )

        source_items.append(
            f"""
            <li>
                <strong>
                    Source {source['number']}:
                </strong>

                <a
                    href="{url}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    {title}
                </a>
            </li>
            """
        )

    return "\n".join(
        source_items
    )


# ---------------------------------------------------------
# Web page
# ---------------------------------------------------------

def page_html(
    question="",
    retrieval_method="semantic",
    answer="",
    sources="",
    error=""
):
    safe_question = html.escape(
        question
    )

    semantic_selected = (
        "selected"
        if retrieval_method == "semantic"
        else ""
    )

    bm25_selected = (
        "selected"
        if retrieval_method == "bm25"
        else ""
    )

    method_label = (
        "Semantic / Vector Search"
        if retrieval_method == "semantic"
        else "BM25 Keyword Search"
    )

    answer_section = ""

    if answer:
        answer_section = f"""
        <div class="answer-box">

            <div class="method-badge">
                Retrieval method:
                <strong>
                    {method_label}
                </strong>
            </div>

            <h2>Answer</h2>

            <div class="answer-text">
                {answer}
            </div>

            <h3>Sources</h3>

            <ul class="sources">
                {sources}
            </ul>

        </div>
        """

    error_section = ""

    if error:
        error_section = f"""
        <div class="error-box">
            {html.escape(error)}
        </div>
        """

    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="UTF-8">

        <title>
            FastAPI Documentation Assistant
        </title>

        <style>

            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f6f8;
                margin: 0;
                color: #222;
            }}

            .container {{
                max-width: 900px;
                margin: 60px auto;
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow:
                    0 4px 15px rgba(0,0,0,0.1);
            }}

            h1 {{
                color: #009688;
                margin-top: 0;
            }}

            textarea {{
                width: 100%;
                min-height: 120px;
                padding: 15px;
                font-size: 16px;
                border: 1px solid #aaa;
                border-radius: 8px;
                box-sizing: border-box;
                resize: vertical;
            }}

            select {{
                width: 100%;
                padding: 12px;
                margin-top: 15px;
                font-size: 16px;
                border: 1px solid #aaa;
                border-radius: 8px;
                background: white;
            }}

            button {{
                margin-top: 15px;
                padding: 12px 24px;
                font-size: 16px;
                background-color: #009688;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
            }}

            button:hover {{
                background-color: #00796b;
            }}

            .answer-box {{
                margin-top: 30px;
                padding: 25px;
                background-color: #f8f9fa;
                border-radius: 10px;
                border: 1px solid #e2e5e8;
            }}

            .method-badge {{
                display: inline-block;
                margin-bottom: 20px;
                padding: 8px 12px;
                background: #e0f2f1;
                color: #00695c;
                border-radius: 6px;
            }}

            .answer-text {{
                line-height: 1.6;
            }}

            .answer-text p {{
                margin-bottom: 16px;
            }}

            pre {{
                background: #1e1e1e;
                color: #f5f5f5;
                padding: 18px;
                border-radius: 8px;
                overflow-x: auto;
                line-height: 1.5;
            }}

            code {{
                font-family:
                    Consolas,
                    Monaco,
                    monospace;
            }}

            p code {{
                background: #e8ecef;
                padding: 2px 5px;
                border-radius: 4px;
            }}

            .citation {{
                color: #00796b;
                font-weight: bold;
            }}

            .sources li {{
                margin-bottom: 10px;
            }}

            a {{
                color: #00796b;
            }}

            .error-box {{
                margin-top: 25px;
                padding: 15px;
                background: #ffecec;
                border: 1px solid #e2a1a1;
                border-radius: 8px;
                color: #8a1f1f;
            }}

        </style>

    </head>

    <body>

        <div class="container">

            <h1>
                FastAPI Documentation Assistant
            </h1>

            <p>
                Ask a technical question about FastAPI.
            </p>

            <form
                method="post"
                action="/ask"
            >

                <textarea
                    name="question"
                    placeholder="Ask a FastAPI question..."
                    required
                >{safe_question}</textarea>

                <select
                    name="retrieval_method"
                >

                    <option
                        value="semantic"
                        {semantic_selected}
                    >
                        Semantic / Vector Search
                    </option>

                    <option
                        value="bm25"
                        {bm25_selected}
                    >
                        BM25 Keyword Search
                    </option>

                </select>

                <button type="submit">
                    Ask
                </button>

            </form>

            {error_section}

            {answer_section}

        </div>

    </body>

    </html>
    """


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------

@app.get(
    "/",
    response_class=HTMLResponse
)
def home():
    return page_html()


@app.post(
    "/ask",
    response_class=HTMLResponse
)
def ask(
    question: str = Form(...),
    retrieval_method: str = Form(
        "semantic"
    ),
):
    try:

        # Semantic retrieval
        if retrieval_method == "semantic":

            results = semantic_search(
                question,
                embedding_model,
                chunks,
                embeddings,
                top_k=TOP_K,
            )

        # BM25 retrieval
        elif retrieval_method == "bm25":

            results = bm25_search(
                question,
                bm25_index,
                chunks,
                top_k=TOP_K,
            )

        else:

            return page_html(
                question=question,
                error=(
                    "Unknown retrieval method."
                ),
            )

        source_map = build_source_map(
            results
        )

        answer = generate_answer(
            question,
            results,
            source_map,
        )

        cited_numbers = (
            extract_cited_source_numbers(
                answer
            )
        )

        formatted_answer = format_answer(
            answer
        )

        sources = build_source_html(
            source_map,
            cited_numbers
        )

        return page_html(
            question=question,
            retrieval_method=retrieval_method,
            answer=formatted_answer,
            sources=sources,
        )

    except Exception as error:

        return page_html(
            question=question,
            retrieval_method=retrieval_method,
            error=f"An error occurred: {error}",
        )