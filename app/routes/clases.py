from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.database import get_connection
from fastapi import status
from typing import Optional
from app.deps import login_required
router = APIRouter(
    prefix="/clases",
    tags=["Clases"],
    dependencies=[Depends(login_required)]
)

templates = Jinja2Templates(directory="app/templates")

@router.get("/")
def listar_clases(request: Request, page: int = 1):

    limit = 20
    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # =========================
    # TOTAL DE REGISTROS
    # =========================
    cursor.execute("SELECT COUNT(*) AS total FROM clase")
    total = cursor.fetchone()["total"]
    total_pages = (total + limit - 1) // limit


    # =========================
    # REGISTROS PAGINADOS
    # =========================
    cursor.execute("""
        SELECT c.*,
        (
            SELECT COUNT(*)
            FROM horario h
            WHERE h.id_clase = c.id_clase AND h.activo = TRUE
        ) AS total_horarios
        FROM clase c
        ORDER BY c.id_clase DESC
        LIMIT %s OFFSET %s
    """, (limit, offset))

    clases = cursor.fetchall()

    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        "clases/list.html",
        {
            "request": request,
            "clases": clases,
            "page": page,
            "total_pages": total_pages
        }
    )

#CREAR CLASE
@router.get("/nuevo")
def nueva_clase_form(request: Request):
    return templates.TemplateResponse(
        "clases/form.html",
        {"request": request, "clase": None}
    )


@router.post("/nuevo")
def nueva_clase_post(
    nombre: str = Form(...),
    descripcion: str = Form(None)
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO clase (nombre, descripcion)
        VALUES (%s, %s)
    """, (nombre, descripcion))

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse("/clases/", status_code=303)
 
 #DETALLE DE CLASE
@router.get("/{id_clase}")
def detalle_clase(request: Request, id_clase: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM clase WHERE id_clase = %s",
        (id_clase,)
    )
    clase = cursor.fetchone()

    cursor.execute("""
        SELECT *
        FROM horario
        WHERE id_clase = %s
        ORDER BY FIELD(dia_semana,
            'Lunes','Martes','Miércoles','Jueves',
            'Viernes','Sábado','Domingo'),
            hora_inicio
    """, (id_clase,))
    horarios = cursor.fetchall()

    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        "clases/detail.html",
        {
            "request": request,
            "clase": clase,
            "horarios": horarios
        }
    )

#EDITAR CLASE
@router.get("/{id_clase}/editar")
def editar_clase_form(request: Request, id_clase: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM clase WHERE id_clase = %s",
        (id_clase,)
    )
    clase = cursor.fetchone()

    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        "clases/form.html",
        {"request": request, "clase": clase}
    )


@router.post("/{id_clase}/editar")
def editar_clase(
    id_clase: int,
    nombre: str = Form(...),
    activo: Optional[str] = Form(None)
):
    activo_bool = activo is not None  # checkbox marcado o no

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE clase
        SET nombre = %s, activo = %s
        WHERE id_clase = %s
    """, (nombre, activo_bool, id_clase))

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(f"/clases/{id_clase}", status_code=303)

#AGREGAR HORARIO A CLASE
@router.post("/{id_clase}/horarios")
def agregar_horario(
    id_clase: int,
    dia_semana: str = Form(...),
    hora_inicio: str = Form(...),
    hora_fin: str = Form(...)
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO horario (
            dia_semana, hora_inicio, hora_fin, id_clase
        )
        VALUES (%s,%s,%s,%s)
    """, (dia_semana, hora_inicio, hora_fin, id_clase))

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(
    url=f"/clases/{id_clase}",
    status_code=303
)

#ELIMINAR HORARIO DE LA CLASE
@router.post("/horarios/{id_horario}/eliminar")
def eliminar_horario(id_horario: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id_clase
        FROM horario
        WHERE id_horario = %s
    """, (id_horario,))
    horario = cursor.fetchone()

    if not horario:
        conn.close()
        return RedirectResponse("/clases", status_code=303)

    id_clase = horario["id_clase"]

    cursor.execute("""
        DELETE FROM horario
        WHERE id_horario = %s
    """, (id_horario,))
    conn.commit()
    conn.close()

    return RedirectResponse(
        f"/clases/{id_clase}",
        status_code=303
    )
