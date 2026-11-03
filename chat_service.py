from database import (
    create_chat,
    save_message,
)


# ============================================================
# CHAT TITLE
# ============================================================

def make_chat_title(
    question: str,
):
    """
    Create a short title from the user's question.
    """

    clean_question = (
        question
        .strip()
        .replace("\n", " ")
    )

    if len(clean_question) <= 55:
        return clean_question

    return (
        clean_question[:52]
        + "..."
    )


# ============================================================
# SAVE NORMAL RAG CHAT
# ============================================================

def save_rag_chat(
    user_id: int,
    question: str,
    result: dict,
):
    """
    Save one user question and one AI answer.
    """

    title = make_chat_title(
        question
    )

    chat_id = create_chat(
        user_id,
        title,
    )


    # --------------------------------------------------------
    # USER MESSAGE
    # --------------------------------------------------------

    save_message(
        chat_id=chat_id,
        role="user",
        content=question,
    )


    # --------------------------------------------------------
    # ASSISTANT MESSAGE
    # --------------------------------------------------------

    save_message(
        chat_id=chat_id,
        role="assistant",
        content=result["answer"],
        retrieval_method=result["method"],
        sources=result["sources"],
        retrieval_ms=result["retrieval_ms"],
        generation_ms=result["generation_ms"],
        total_ms=result["total_ms"],
    )


    return chat_id


# ============================================================
# SAVE COMPARE CHAT
# ============================================================

def save_compare_chat(
    user_id: int,
    question: str,
    semantic_result: dict,
    bm25_result: dict,
):
    """
    Save one user question and both Compare-mode answers.
    """

    title = make_chat_title(
        question
    )

    chat_id = create_chat(
        user_id,
        title,
    )


    # --------------------------------------------------------
    # USER MESSAGE
    # --------------------------------------------------------

    save_message(
        chat_id=chat_id,
        role="user",
        content=question,
    )


    # --------------------------------------------------------
    # SEMANTIC ANSWER
    # --------------------------------------------------------

    save_message(
        chat_id=chat_id,
        role="assistant",
        content=semantic_result["answer"],
        retrieval_method="semantic",
        sources=semantic_result["sources"],
        retrieval_ms=semantic_result["retrieval_ms"],
        generation_ms=semantic_result["generation_ms"],
        total_ms=semantic_result["total_ms"],
    )


    # --------------------------------------------------------
    # BM25 ANSWER
    # --------------------------------------------------------

    save_message(
        chat_id=chat_id,
        role="assistant",
        content=bm25_result["answer"],
        retrieval_method="bm25",
        sources=bm25_result["sources"],
        retrieval_ms=bm25_result["retrieval_ms"],
        generation_ms=bm25_result["generation_ms"],
        total_ms=bm25_result["total_ms"],
    )


    return chat_id