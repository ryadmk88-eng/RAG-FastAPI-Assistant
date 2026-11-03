from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request,
)

from auth import get_logged_in_user

from database import (
    get_connection,
    save_feedback,
)


router = APIRouter()


# ============================================================
# SAVE ANSWER FEEDBACK
# ============================================================

@router.post(
    "/api/messages/{message_id}/feedback"
)
async def submit_feedback(
    message_id: int,
    request: Request,
    helpful: int = Form(...),
):

    user = get_logged_in_user(
        request
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Please sign in first.",
        )


    if helpful not in (
        0,
        1,
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid feedback value.",
        )


    # --------------------------------------------------------
    # Make sure this assistant message belongs
    # to the logged-in user's chat.
    # --------------------------------------------------------

    connection = get_connection()

    try:

        message = connection.execute(
            """
            SELECT
                messages.id
            FROM messages
            JOIN chats
                ON chats.id = messages.chat_id
            WHERE
                messages.id = ?
                AND messages.role = 'assistant'
                AND chats.user_id = ?
            """,
            (
                message_id,
                user["id"],
            ),
        ).fetchone()

    finally:

        connection.close()


    if not message:

        raise HTTPException(
            status_code=404,
            detail="Assistant message not found.",
        )


    save_feedback(
        message_id,
        user["id"],
        helpful,
    )


    return {
        "success": True,
        "message_id": message_id,
        "helpful": bool(helpful),
    }