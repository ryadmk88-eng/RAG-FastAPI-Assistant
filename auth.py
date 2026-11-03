from database import (
    create_user,
    get_user_by_email,
    get_user_by_id,
)

from pwdlib import PasswordHash


# ============================================================
# PASSWORD HASHING
# ============================================================

password_hash = PasswordHash.recommended()


def hash_password(
    password: str,
):
    """
    Convert a plain-text password
    into a secure password hash.
    """

    return password_hash.hash(
        password
    )


def verify_password(
    plain_password: str,
    hashed_password: str,
):
    """
    Check whether a plain password
    matches the stored password hash.
    """

    try:
        return password_hash.verify(
            plain_password,
            hashed_password,
        )

    except Exception:
        return False


# ============================================================
# REGISTRATION VALIDATION
# ============================================================

def validate_registration(
    name: str,
    email: str,
    password: str,
    confirm_password: str,
):
    name = name.strip()
    email = email.strip().lower()

    if not name:
        return (
            False,
            "Please enter your name.",
        )

    if len(name) < 2:
        return (
            False,
            "Your name must contain "
            "at least 2 characters.",
        )

    if not email:
        return (
            False,
            "Please enter your email address.",
        )

    if (
        "@" not in email
        or "." not in email
    ):
        return (
            False,
            "Please enter a valid email address.",
        )

    if len(password) < 8:
        return (
            False,
            "Your password must contain "
            "at least 8 characters.",
        )

    if password != confirm_password:
        return (
            False,
            "The passwords do not match.",
        )

    existing_user = (
        get_user_by_email(
            email
        )
    )

    if existing_user:
        return (
            False,
            "An account with this email "
            "already exists.",
        )

    return (
        True,
        None,
    )


# ============================================================
# CREATE ACCOUNT
# ============================================================

def register_user(
    name: str,
    email: str,
    password: str,
):
    """
    Create a user using a hashed password.
    The plain password is never stored.
    """

    clean_name = (
        name.strip()
    )

    clean_email = (
        email.strip().lower()
    )

    hashed_password = (
        hash_password(
            password
        )
    )

    user_id = create_user(
        clean_name,
        clean_email,
        hashed_password,
    )

    return get_user_by_id(
        user_id
    )


# ============================================================
# LOGIN
# ============================================================

def authenticate_user(
    email: str,
    password: str,
):
    """
    Return the user when the email
    and password are correct.

    Return None when authentication fails.
    """

    clean_email = (
        email.strip().lower()
    )

    user = get_user_by_email(
        clean_email
    )

    if not user:
        return None

    password_is_valid = (
        verify_password(
            password,
            user["password_hash"],
        )
    )

    if not password_is_valid:
        return None

    return user


# ============================================================
# SESSION HELPERS
# ============================================================

def login_user(
    request,
    user_id: int,
):
    """
    Store the logged-in user's ID
    inside the browser session.

    SessionMiddleware will be added
    to main.py later.
    """

    request.session[
        "user_id"
    ] = user_id


def logout_user(
    request,
):
    """
    Remove login information
    from the browser session.
    """

    request.session.clear()


def get_logged_in_user(
    request,
):
    """
    Return the current logged-in user.

    Returns None when the visitor
    is not signed in.
    """

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:
        return None

    return get_user_by_id(
        user_id
    )


# ============================================================
# AUTH TEST
# ============================================================

if __name__ == "__main__":

    test_password = (
        "TestPassword123!"
    )

    hashed = hash_password(
        test_password
    )

    print(
        "Password hashing test:"
    )

    print(
        "Plain password:",
        test_password,
    )

    print(
        "Stored hash:",
        hashed,
    )

    print(
        "Correct password:",
        verify_password(
            test_password,
            hashed,
        ),
    )

    print(
        "Wrong password:",
        verify_password(
            "wrong-password",
            hashed,
        ),
    )