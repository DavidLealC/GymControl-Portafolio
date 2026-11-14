from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from app.database import get_connection
from fastapi.responses import RedirectResponse
from fastapi import status
from app.deps import login_required
router = APIRouter(prefix="/descuentos", tags=["Descuentos"], dependencies=[Depends(login_required)])
templates = Jinja2Templates(directory="app/templates")

# LISTAR
@router.get("", dependencies=[Depends(login_required)])
def listar_descuentos(request: Request):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM descuento")
    descuentos = cursor.fetchall()

    cursor.close()
    conn.close()
    return templates.TemplateResponse(
        "descuentos/list.html",
        {"request": request, "descuentos": descuentos}
    )

# FORM CREAR
@router.get("/nuevo")
def nuevo_descuento(request: Request):
    return templates.TemplateResponse(
        "descuentos/form.html",
        {"request": request, "descuento": None}
    )

# CREAR
@router.post("/crear")
def crear_descuento(
    nombre: str = Form(...),
    porcentaje: float = Form(...),
    activo: int = Form(1)
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO descuento (nombre, porcentaje, activo) VALUES (%s, %s, %s)",
        (nombre, porcentaje, activo)
    )

    conn.commit()
    cursor.close()
    conn.close()
    return RedirectResponse("/descuentos", status_code=303)

# FORM EDITAR
@router.get("/{id_descuento}/editar")
def editar_descuento(request: Request, id_descuento: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM descuento WHERE id_descuento = %s",
        (id_descuento,)
    )
    descuento = cursor.fetchone()

    cursor.close()
    conn.close()
    return templates.TemplateResponse(
        "descuentos/form.html",
        {"request": request, "descuento": descuento}
    )

# ACTUALIZAR
@router.post("/actualizar/{id_descuento}")
def actualizar_descuento(
    id_descuento: int,
    nombre: str = Form(...),
    porcentaje: float = Form(...),
    activo: int = Form(1)
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE descuento
        SET nombre=%s, porcentaje=%s, activo=%s
        WHERE id_descuento=%s
        """,
        (nombre, porcentaje, activo, id_descuento)
    )

    conn.commit()
    cursor.close()
    conn.close()
    return RedirectResponse("/descuentos", status_code=303)

# ELIMINAR
@router.post("/eliminar/{id_descuento}")
def eliminar_descuento(id_descuento: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM descuento WHERE id_descuento=%s",
        (id_descuento,)
    )

    conn.commit()
    cursor.close()
    conn.close()
    return RedirectResponse("/descuentos", status_code=303)
