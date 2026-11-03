from pathlib import Path

from fastapi import (
    APIRouter,
    Form,
    Request,
)

from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)

from fastapi.templating import (
    Jinja2Templates,
)

from auth import (
    authenticate_user,
    get_logged_in_user,
    login_user,
    logout_user,
    register_user,
    validate_registration,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent

TEMPLATES_DIR = (
    BASE_DIR
    / "templates"
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()

templates = Jinja2Templates(
    directory=str(
        TEMPLATES_DIR
    )
)


# ============================================================
# LOGIN PAGE
# ============================================================

@router.get(
    "/login",
    response_class=HTMLResponse,
)
async def login_page(
    request: Request,
):
    registered = (
        request.query_params.get(
            "registered"
        )
    )

    success = None

    if registered == "1":
        success = (
            "Account created successfully. "
            "You can now sign in."
        )

    return templates.TemplateResponse(
        request=request,
        name="auth.html",
        context={
            "mode": "login",
            "error": None,
            "success": success,
            "name": "",
            "email": "",
        },
    )


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_class=HTMLResponse,
)
async def login_account(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    user = authenticate_user(
        email,
        password,
    )

    if not user:

        return templates.TemplateResponse(
            request=request,
            name="auth.html",
            context={
                "mode": "login",
                "error":
                    (
                        "Incorrect email "
                        "or password."
                    ),
                "success": None,
                "name": "",
                "email": email,
            },
            status_code=400,
        )

    login_user(
        request,
        user["id"],
    )

    return RedirectResponse(
        url="/",
        status_code=303,
    )


# ============================================================
# REGISTER PAGE
# ============================================================

@router.get(
    "/register",
    response_class=HTMLResponse,
)
async def register_page(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="auth.html",
        context={
            "mode": "register",
            "error": None,
            "success": None,
            "name": "",
            "email": "",
        },
    )


# ============================================================
# REGISTER ACCOUNT
# ============================================================

@router.post(
    "/register",
    response_class=HTMLResponse,
)
async def register_account(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    (
        valid,
        error,
    ) = validate_registration(
        name,
        email,
        password,
        confirm_password,
    )

    if not valid:

        return templates.TemplateResponse(
            request=request,
            name="auth.html",
            context={
                "mode": "register",
                "error": error,
                "success": None,
                "name": name,
                "email": email,
            },
            status_code=400,
        )

    try:

        register_user(
            name,
            email,
            password,
        )

    except Exception as exc:

        print(
            "Registration error:",
            repr(exc),
        )

        return templates.TemplateResponse(
            request=request,
            name="auth.html",
            context={
                "mode": "register",
                "error":
                    (
                        "The account could not "
                        "be created. "
                        "Please try again."
                    ),
                "success": None,
                "name": name,
                "email": email,
            },
            status_code=500,
        )

    return RedirectResponse(
        url="/login?registered=1",
        status_code=303,
    )


# ============================================================
# CURRENT USER
# ============================================================

@router.get(
    "/api/me"
)
async def current_user(
    request: Request,
):
    user = get_logged_in_user(
        request
    )

    if not user:

        return {
            "authenticated": False,
        }

    return {
        "authenticated": True,
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
    }


# ============================================================
# LOGOUT
# ============================================================

@router.post(
    "/logout"
)
async def logout(
    request: Request,
):
    logout_user(
        request
    )

    return {
        "success": True,
    }