from database import (
    delete_chat,
    get_connection,
)


# ============================================================
# DATABASE MIGRATION
# ============================================================

def ensure_chat_management_schema():
    """
    Add the pinned column to existing databases
    without deleting any existing chats.
    """

    connection = get_connection()

    try:
        columns = connection.execute(
            """
            PRAGMA table_info(chats)
            """
        ).fetchall()

        column_names = {
            column["name"]
            for column in columns
        }

        if "pinned" not in column_names:

            connection.execute(
                """
                ALTER TABLE chats
                ADD COLUMN pinned INTEGER
                NOT NULL DEFAULT 0
                """
            )

            connection.commit()

    finally:
        connection.close()


ensure_chat_management_schema()


# ============================================================
# LIST CHATS
# ============================================================

def get_managed_chats(
    user_id: int,
):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                user_id,
                title,
                pinned,
                created_at,
                updated_at

            FROM chats

            WHERE user_id = ?

            ORDER BY
                pinned DESC,
                updated_at DESC,
                id DESC
            """,
            (
                user_id,
            ),
        ).fetchall()

        return rows

    finally:
        connection.close()


# ============================================================
# GET ONE CHAT
# ============================================================

def get_managed_chat(
    chat_id: int,
    user_id: int,
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                user_id,
                title,
                pinned,
                created_at,
                updated_at

            FROM chats

            WHERE id = ?
            AND user_id = ?
            """,
            (
                chat_id,
                user_id,
            ),
        ).fetchone()

        return row

    finally:
        connection.close()


# ============================================================
# RENAME CHAT
# ============================================================

def rename_managed_chat(
    chat_id: int,
    user_id: int,
    new_title: str,
):
    clean_title = (
        new_title.strip()
    )

    if not clean_title:
        return False

    if len(clean_title) > 120:
        clean_title = clean_title[:120]

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE chats

            SET
                title = ?,
                updated_at = CURRENT_TIMESTAMP

            WHERE id = ?
            AND user_id = ?
            """,
            (
                clean_title,
                chat_id,
                user_id,
            ),
        )

        connection.commit()

        return (
            cursor.rowcount > 0
        )

    finally:
        connection.close()


# ============================================================
# PIN / UNPIN
# ============================================================

def set_chat_pinned(
    chat_id: int,
    user_id: int,
    pinned: bool,
):
    pinned_value = (
        1
        if pinned
        else 0
    )

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE chats

            SET
                pinned = ?,
                updated_at = CURRENT_TIMESTAMP

            WHERE id = ?
            AND user_id = ?
            """,
            (
                pinned_value,
                chat_id,
                user_id,
            ),
        )

        connection.commit()

        return (
            cursor.rowcount > 0
        )

    finally:
        connection.close()


# ============================================================
# DELETE
# ============================================================

def delete_managed_chat(
    chat_id: int,
    user_id: int,
):
    return delete_chat(
        chat_id,
        user_id,
    )