"""Protección CSRF para los formularios basados en sesiones de GymControl."""

import secrets
from fastapi import HTTPException, Request

TOKEN_KEY = "_csrf_token"
UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
FORM_CONTENT_TYPES = frozenset({"application/x-www-form-urlencoded", "multipart/form-data"})


async def csrf_guard(request: Request) -> None:
    """Genera el token en visitas normales y lo valida en peticiones mutadoras.

    El token se almacena en la sesión firmada por Starlette. Los formularios HTML
    envían el mismo valor como campo oculto; clientes JSON pueden usar el header
    X-CSRF-Token. Un POST sin sesión/token válido se rechaza antes de llegar a la BD.
    """
    session = request.session
    if request.method not in UNSAFE_METHODS:
        if not session.get(TOKEN_KEY):
            session[TOKEN_KEY] = secrets.token_urlsafe(32)
        return

    expected = session.get(TOKEN_KEY)
    if not isinstance(expected, str) or not expected:
        raise HTTPException(status_code=403, detail="Token CSRF inválido o ausente")

    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type in FORM_CONTENT_TYPES:
        form = await request.form()
        actual = form.get(TOKEN_KEY)
    else:
        actual = request.headers.get("X-CSRF-Token")

    if not isinstance(actual, str) or not secrets.compare_digest(actual, expected):
        raise HTTPException(status_code=403, detail="Token CSRF inválido o ausente")
