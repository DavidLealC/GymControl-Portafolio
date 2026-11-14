from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

def login_required(request: Request):
    if "user" not in request.session:
        raise HTTPException(status_code=302, headers={"Location": "/login"})