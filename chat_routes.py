from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request,
)

from auth import (
    get_logged_in_user,
)

from chat_management import (
    delete_managed_chat,
    get_managed_chat,
    get_managed_chats,
    rename_managed_chat,
    set_chat_pinned,
)

from database import (
    get_chat_messages,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# LIST CHATS
# ============================================================

@router.get(
    "/api/chats"
)
async def list_chats(
    request: Request,
):
    user = get_logged_in_user(
        request
    )

    if not user:
        return {
            "authenticated": False,
            "chats": [],
        }

    chats = get_managed_chats(
        user["id"]
    )

    return {
        "authenticated": True,

        "chats": [
            {
                "id": chat["id"],
                "title": chat["title"],
                "pinned": bool(
                    chat["pinned"]
                ),
                "created_at":
                    chat["created_at"],
                "updated_at":
                    chat["updated_at"],
            }
            for chat in chats
        ],
    }


# ============================================================
# GET ONE CHAT
# ============================================================

@router.get(
    "/api/chats/{chat_id}"
)
async def read_chat(
    chat_id: int,
    request: Request,
):
    user = get_logged_in_user(
        request
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Please sign in.",
        )

    chat = get_managed_chat(
        chat_id,
        user["id"],
    )

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found.",
        )

    messages = get_chat_messages(
        chat_id
    )

    return {
        "chat": {
            "id": chat["id"],
            "title": chat["title"],
            "pinned": bool(
                chat["pinned"]
            ),
            "created_at":
                chat["created_at"],
            "updated_at":
                chat["updated_at"],
        },

        "messages": messages,
    }


# ============================================================
# RENAME CHAT
# ============================================================

@router.post(
    "/api/chats/{chat_id}/rename"
)
async def rename_chat_route(
    chat_id: int,
    request: Request,
    title: str = Form(...),
):
    user = get_logged_in_user(
        request
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Please sign in.",
        )

    chat = get_managed_chat(
        chat_id,
        user["id"],
    )

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found.",
        )

    renamed = rename_managed_chat(
        chat_id,
        user["id"],
        title,
    )

    if not renamed:
        raise HTTPException(
            status_code=400,
            detail="Chat title could not be updated.",
        )

    return {
        "success": True,
    }


# ============================================================
# PIN CHAT
# ============================================================

@router.post(
    "/api/chats/{chat_id}/pin"
)
async def pin_chat_route(
    chat_id: int,
    request: Request,
):
    user = get_logged_in_user(
        request
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Please sign in.",
        )

    chat = get_managed_chat(
        chat_id,
        user["id"],
    )

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found.",
        )

    new_pinned_value = (
        not bool(
            chat["pinned"]
        )
    )

    changed = set_chat_pinned(
        chat_id,
        user["id"],
        new_pinned_value,
    )

    if not changed:
        raise HTTPException(
            status_code=500,
            detail="Pin status could not be updated.",
        )

    return {
        "success": True,
        "pinned": new_pinned_value,
    }


# ============================================================
# DELETE ONE CHAT
# ============================================================

@router.delete(
    "/api/chats/{chat_id}"
)
async def remove_chat(
    chat_id: int,
    request: Request,
):
    user = get_logged_in_user(
        request
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Please sign in.",
        )

    chat = get_managed_chat(
        chat_id,
        user["id"],
    )

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found.",
        )

    deleted = delete_managed_chat(
        chat_id,
        user["id"],
    )

    if not deleted:
        raise HTTPException(
            status_code=500,
            detail="Chat could not be deleted.",
        )

    return {
        "success": True,
        "deleted_chat_id": chat_id,
    }


# ============================================================
# CLEAR ALL CHAT HISTORY
# ============================================================

@router.delete(
    "/api/chats"
)
async def clear_chat_history(
    request: Request,
):
    user = get_logged_in_user(
        request
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Please sign in.",
        )

    chats = get_managed_chats(
        user["id"]
    )

    deleted_count = 0

    for chat in chats:

        deleted = delete_managed_chat(
            chat["id"],
            user["id"],
        )

        if deleted:
            deleted_count += 1

    return {
        "success": True,
        "deleted_count": deleted_count,
    }