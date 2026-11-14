from fastapi import APIRouter, Request, Form
import secrets
from fastapi.responses import RedirectResponse
from app.database import get_connection
from app.security import verify_password
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login")
def login(request: Request, usuario: str = Form(...), password: str = Form(...)):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM usuario_sistema WHERE usuario=%s AND activo=1",
        (usuario,)
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user or not verify_password(password, user["password"]):
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Credenciales incorrectas"}
        )

    # El inicio de sesión renueva el token e invalida el estado anónimo anterior.
    request.session.clear()
    request.session["user"] = user["usuario"]
    request.session["_csrf_token"] = secrets.token_urlsafe(32)

    return RedirectResponse("/", status_code=302)

@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)