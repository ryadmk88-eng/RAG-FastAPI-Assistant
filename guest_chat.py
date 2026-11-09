import sqlite3
import time
import uuid
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

GUEST_DB = (
    BASE_DIR
    / "data"
    / "guest_chats.db"
)

GUEST_QUESTION_LIMIT = 5
GUEST_RESET_SECONDS = 2 * 60 * 60


def init_guest_store():
    connection = sqlite3.connect(
        GUEST_DB
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS guest_turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_token TEXT NOT NULL,
            turn_html TEXT NOT NULL,
            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()


def _delete_guest_turns(
    guest_token,
):
    connection = sqlite3.connect(
        GUEST_DB
    )

    connection.execute(
        """
        DELETE FROM guest_turns
        WHERE guest_token = ?
        """,
        (guest_token,),
    )

    connection.commit()
    connection.close()


def prepare_guest_session(
    request,
):
    now = int(time.time())

    guest_token = request.session.get(
        "guest_token"
    )

    guest_started = request.session.get(
        "guest_started"
    )

    guest_count = request.session.get(
        "guest_count",
        0,
    )

    expired = (
        not guest_started
        or now - guest_started
        >= GUEST_RESET_SECONDS
    )

    if (
        not guest_token
        or expired
    ):
        if guest_token:
            _delete_guest_turns(
                guest_token
            )

        guest_token = uuid.uuid4().hex

        guest_started = now
        guest_count = 0

        request.session[
            "guest_token"
        ] = guest_token

        request.session[
            "guest_started"
        ] = guest_started

        request.session[
            "guest_count"
        ] = 0

    return (
        guest_token,
        guest_count,
    )


def guest_limit_reached(
    request,
):
    _guest_token, guest_count = (
        prepare_guest_session(
            request
        )
    )

    return (
        guest_count
        >= GUEST_QUESTION_LIMIT
    )


def get_guest_history(
    request,
):
    guest_token, _guest_count = (
        prepare_guest_session(
            request
        )
    )

    connection = sqlite3.connect(
        GUEST_DB
    )

    rows = connection.execute(
        """
        SELECT turn_html
        FROM guest_turns
        WHERE guest_token = ?
        ORDER BY id ASC
        """,
        (guest_token,),
    ).fetchall()

    connection.close()

    return "".join(
        row[0]
        for row in rows
    )


def save_guest_turn(
    request,
    turn_html,
):
    guest_token, guest_count = (
        prepare_guest_session(
            request
        )
    )

    connection = sqlite3.connect(
        GUEST_DB
    )

    connection.execute(
        """
        INSERT INTO guest_turns (
            guest_token,
            turn_html
        )
        VALUES (?, ?)
        """,
        (
            guest_token,
            turn_html,
        ),
    )

    connection.commit()
    connection.close()

    request.session[
        "guest_count"
    ] = guest_count + 1