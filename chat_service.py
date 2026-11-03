from database import (
    create_chat,
    get_chat,
    save_message,
)


# ============================================================
# CHAT TITLE
# ============================================================

def make_chat_title(
    question: str,
) -> str:
    clean = (
        question
        .strip()
        .replace("\n", " ")
    )

    if len(clean) <= 55:
        return clean

    return (
        clean[:52]
        .rstrip()
        + "..."
    )


# ============================================================
# GET OR CREATE CHAT
# ============================================================

def get_or_create_chat(
    user_id: int,
    question: str,
    chat_id: int | None = None,
):
    """
    Reuse an existing chat when chat_id belongs to the user.
    Otherwise create a new chat.
    """

    if chat_id is not None:

        existing_chat = get_chat(
            chat_id,
            user_id,
        )

        if existing_chat:
            return chat_id


    title = make_chat_title(
        question
    )

    return create_chat(
        user_id,
        title,
    )


# ============================================================
# SAVE NORMAL RAG CHAT
# ============================================================

def save_rag_chat(
    user_id: int,
    question: str,
    result: dict,
    chat_id: int | None = None,
):
    """
    Save one user question and one assistant response.

    If chat_id is supplied and belongs to the user,
    append the messages to that existing conversation.
    """

    actual_chat_id = (
        get_or_create_chat(
            user_id,
            question,
            chat_id,
        )
    )


    save_message(
        chat_id=actual_chat_id,
        role="user",
        content=question,
    )


    save_message(
        chat_id=actual_chat_id,
        role="assistant",
        content=result["answer"],
        retrieval_method=result["method"],
        sources=result["sources"],
        retrieval_ms=result["retrieval_ms"],
        generation_ms=result["generation_ms"],
        total_ms=result["total_ms"],
    )


    return actual_chat_id


# ============================================================
# SAVE COMPARE CHAT
# ============================================================

def save_compare_chat(
    user_id: int,
    question: str,
    semantic_result: dict,
    bm25_result: dict,
    chat_id: int | None = None,
):
    """
    Save one user question followed by both
    Semantic and BM25 responses.

    If chat_id is supplied and belongs to the user,
    append everything to that existing conversation.
    """

    actual_chat_id = (
        get_or_create_chat(
            user_id,
            question,
            chat_id,
        )
    )


    save_message(
        chat_id=actual_chat_id,
        role="user",
        content=question,
    )


    save_message(
        chat_id=actual_chat_id,
        role="assistant",
        content=semantic_result["answer"],
        retrieval_method=semantic_result["method"],
        sources=semantic_result["sources"],
        retrieval_ms=semantic_result["retrieval_ms"],
        generation_ms=semantic_result["generation_ms"],
        total_ms=semantic_result["total_ms"],
    )


    save_message(
        chat_id=actual_chat_id,
        role="assistant",
        content=bm25_result["answer"],
        retrieval_method=bm25_result["method"],
        sources=bm25_result["sources"],
        retrieval_ms=bm25_result["retrieval_ms"],
        generation_ms=bm25_result["generation_ms"],
        total_ms=bm25_result["total_ms"],
    )


    return actual_chat_id