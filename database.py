import json
import sqlite3
from pathlib import Path


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = (
    BASE_DIR
    / "app.db"
)


# ============================================================
# CONNECTION
# ============================================================

def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = (
        sqlite3.Row
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# INITIALISE DATABASE
# ============================================================

def init_db():
    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT NOT NULL UNIQUE,

            password_hash TEXT NOT NULL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


    # --------------------------------------------------------
    # CHATS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            title TEXT NOT NULL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (
                user_id
            )
            REFERENCES users (
                id
            )
            ON DELETE CASCADE
        )
        """
    )


    # --------------------------------------------------------
    # MESSAGES
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            chat_id INTEGER NOT NULL,

            role TEXT NOT NULL
                CHECK (
                    role IN (
                        'user',
                        'assistant'
                    )
                ),

            content TEXT NOT NULL,

            retrieval_method TEXT,

            sources_json TEXT,

            retrieval_ms REAL,

            generation_ms REAL,

            total_ms REAL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (
                chat_id
            )
            REFERENCES chats (
                id
            )
            ON DELETE CASCADE
        )
        """
    )


    # --------------------------------------------------------
    # FEEDBACK
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            message_id INTEGER NOT NULL,

            user_id INTEGER NOT NULL,

            helpful INTEGER NOT NULL
                CHECK (
                    helpful IN (
                        0,
                        1
                    )
                ),

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            UNIQUE (
                message_id,
                user_id
            ),

            FOREIGN KEY (
                message_id
            )
            REFERENCES messages (
                id
            )
            ON DELETE CASCADE,

            FOREIGN KEY (
                user_id
            )
            REFERENCES users (
                id
            )
            ON DELETE CASCADE
        )
        """
    )


    # --------------------------------------------------------
    # INDEXES
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_chats_user_id

        ON chats (
            user_id
        )
        """
    )


    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_messages_chat_id

        ON messages (
            chat_id
        )
        """
    )


    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_feedback_message_id

        ON feedback (
            message_id
        )
        """
    )


    connection.commit()

    connection.close()


# ============================================================
# USERS
# ============================================================

def create_user(
    name,
    email,
    password_hash,
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO users (
                name,
                email,
                password_hash
            )
            VALUES (
                ?,
                ?,
                ?
            )
            """,
            (
                name.strip(),
                email.strip().lower(),
                password_hash,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def get_user_by_email(
    email
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                name,
                email,
                password_hash,
                created_at

            FROM users

            WHERE email = ?
            """,
            (
                email.strip().lower(),
            ),
        ).fetchone()

        return row

    finally:
        connection.close()


def get_user_by_id(
    user_id
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                name,
                email,
                created_at

            FROM users

            WHERE id = ?
            """,
            (
                user_id,
            ),
        ).fetchone()

        return row

    finally:
        connection.close()


# ============================================================
# CHATS
# ============================================================

def create_chat(
    user_id,
    title,
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO chats (
                user_id,
                title
            )
            VALUES (
                ?,
                ?
            )
            """,
            (
                user_id,
                title.strip(),
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def get_user_chats(
    user_id
):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                user_id,
                title,
                created_at,
                updated_at

            FROM chats

            WHERE user_id = ?

            ORDER BY
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


def get_chat(
    chat_id,
    user_id,
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                user_id,
                title,
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


def rename_chat(
    chat_id,
    user_id,
    new_title,
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE chats

            SET
                title = ?,
                updated_at =
                    CURRENT_TIMESTAMP

            WHERE id = ?
            AND user_id = ?
            """,
            (
                new_title.strip(),
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


def delete_chat(
    chat_id,
    user_id,
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM chats

            WHERE id = ?
            AND user_id = ?
            """,
            (
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
# MESSAGES
# ============================================================

def save_message(
    chat_id,
    role,
    content,
    retrieval_method=None,
    sources=None,
    retrieval_ms=None,
    generation_ms=None,
    total_ms=None,
):
    if role not in {
        "user",
        "assistant",
    }:
        raise ValueError(
            "role must be "
            "'user' or 'assistant'"
        )

    sources_json = None

    if sources is not None:
        sources_json = json.dumps(
            sources
        )

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO messages (
                chat_id,
                role,
                content,
                retrieval_method,
                sources_json,
                retrieval_ms,
                generation_ms,
                total_ms
            )
            VALUES (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?
            )
            """,
            (
                chat_id,
                role,
                content,
                retrieval_method,
                sources_json,
                retrieval_ms,
                generation_ms,
                total_ms,
            ),
        )

        connection.execute(
            """
            UPDATE chats

            SET updated_at =
                CURRENT_TIMESTAMP

            WHERE id = ?
            """,
            (
                chat_id,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def get_chat_messages(
    chat_id
):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                chat_id,
                role,
                content,
                retrieval_method,
                sources_json,
                retrieval_ms,
                generation_ms,
                total_ms,
                created_at

            FROM messages

            WHERE chat_id = ?

            ORDER BY
                id ASC
            """,
            (
                chat_id,
            ),
        ).fetchall()

        messages = []

        for row in rows:
            item = dict(row)

            if item[
                "sources_json"
            ]:
                try:
                    item[
                        "sources"
                    ] = json.loads(
                        item[
                            "sources_json"
                        ]
                    )

                except json.JSONDecodeError:
                    item[
                        "sources"
                    ] = None

            else:
                item[
                    "sources"
                ] = None

            messages.append(
                item
            )

        return messages

    finally:
        connection.close()


# ============================================================
# FEEDBACK
# ============================================================

def save_feedback(
    message_id,
    user_id,
    helpful,
):
    helpful_value = (
        1
        if helpful
        else 0
    )

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO feedback (
                message_id,
                user_id,
                helpful
            )
            VALUES (
                ?,
                ?,
                ?
            )

            ON CONFLICT (
                message_id,
                user_id
            )

            DO UPDATE SET
                helpful =
                    excluded.helpful,

                created_at =
                    CURRENT_TIMESTAMP
            """,
            (
                message_id,
                user_id,
                helpful_value,
            ),
        )

        connection.commit()

    finally:
        connection.close()


# ============================================================
# STARTUP TEST
# ============================================================

if __name__ == "__main__":
    init_db()

    print(
        "Database created successfully."
    )

    print(
        f"Database location: "
        f"{DATABASE_PATH}"
    )