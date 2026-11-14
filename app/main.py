from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import os
import sys
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Depends
from app.deps import login_required
from app.csrf import csrf_guard
from dotenv import load_dotenv

from app.routes import (
    clientes_router,
    clases_router,
    horarios_router,
    coaches,
    descuentos,
    historial,
    servicios,
    login
)


load_dotenv()
secret_key = os.getenv("SECRET_KEY", "")
if len(secret_key) < 32:
    raise RuntimeError("Configura SECRET_KEY con al menos 32 caracteres aleatorios en el .env")

# Todas las rutas reciben/verifican el token; también el formulario de login.
app = FastAPI(title="GymControl", dependencies=[Depends(csrf_guard)])

def resource_path(relative_path: str):
    """
    Devuelve ruta correcta tanto en desarrollo como en .exe
    """
    try:
        base_path = sys._MEIPASS  # PyInstaller
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


templates = Jinja2Templates(
    directory=resource_path("app/templates")
)


# DASHBOARD
@app.get("/", dependencies=[Depends(login_required)])
def dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )


# ROUTERS
app.include_router(clientes_router)
app.include_router(clases_router)
app.include_router(horarios_router)
app.include_router(coaches.router)
app.include_router(descuentos.router)
app.include_router(historial.router)
app.include_router(servicios.router)
app.include_router(login.router)

app.add_middleware(
    SessionMiddleware,
    secret_key=secret_key,
    https_only=os.getenv("SESSION_HTTPS_ONLY", "false").strip().lower() == "true",
    same_site="lax",      # protección adicional, no sustituye el token CSRF
    max_age=60 * 60 * 8   # 8 horas de sesión
)
