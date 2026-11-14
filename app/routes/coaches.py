from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from app.database import get_connection
from fastapi.responses import RedirectResponse
from fastapi import status
from app.deps import login_required

router = APIRouter(prefix="/coaches", tags=["Coaches"], dependencies=[Depends(login_required)])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", dependencies=[Depends(login_required)])
def listar_coaches(request: Request, page: int = 1):

    limit = 20
    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # =========================
    # TOTAL DE COACHES (sin JOIN)
    # =========================
    cursor.execute("SELECT COUNT(*) AS total FROM coach")
    total = cursor.fetchone()["total"]
    total_pages = (total + limit - 1) // limit


    # =========================
    # REGISTROS PAGINADOS
    # =========================
    cursor.execute("""
        SELECT 
            c.id_coach,
            c.nombre,
            c.telefono,
            c.activo,
            COUNT(cc.id_clase) AS total_clases
        FROM coach c
        LEFT JOIN clase_coach cc 
            ON cc.id_coach = c.id_coach
        GROUP BY c.id_coach
        ORDER BY c.nombre
        LIMIT %s OFFSET %s
    """, (limit, offset))

    coaches = cursor.fetchall()

    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        "coaches/list.html",
        {
            "request": request,
            "coaches": coaches,
            "page": page,
            "total_pages": total_pages
        }
    )

@router.get("/nuevo")
def nuevo_coach_form(request: Request):
    return templates.TemplateResponse(
        "coaches/new.html",
        {"request": request}
    )

@router.post("/nuevo")
def nuevo_coach_post(
    nombre: str = Form(...),
    telefono: str = Form(None),
    activo: int = Form(1)
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO coach (nombre, telefono, activo)
        VALUES (%s, %s, %s)
    """, (
        nombre,
        telefono,
        activo
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(
        url="/coaches",
        status_code=303
    )

@router.post("/{id_coach}/eliminar")
def eliminar_coach(id_coach: int):
    conn = get_connection()
    cursor = conn.cursor()

    # 1️⃣ Eliminar relaciones con clases
    cursor.execute(
        "DELETE FROM clase_coach WHERE id_coach = %s",
        (id_coach,)
    )

    # 2️⃣ Eliminar coach
    cursor.execute(
        "DELETE FROM coach WHERE id_coach = %s",
        (id_coach,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(
        url="/coaches",
        status_code=303
    )



# =========================
# DETALLE DEL COACH
# =========================
@router.get("/{id_coach}")
def detalle_coach(request: Request, id_coach: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Coach
    cursor.execute(
        "SELECT * FROM coach WHERE id_coach = %s",
        (id_coach,)
    )
    coach = cursor.fetchone()

    if not coach:
        cursor.close()
        conn.close()
        return {"error": "Coach no encontrado"}

    # Clases asignadas al coach
    cursor.execute("""
        SELECT cl.id_clase, cl.nombre, cl.descripcion
        FROM clase cl
        JOIN clase_coach cc 
            ON cc.id_clase = cl.id_clase
        WHERE cc.id_coach = %s
        AND cl.activo = TRUE
        ORDER BY cl.nombre
    """, (id_coach,))

    clases = cursor.fetchall()

    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        "coaches/detail.html",
        {
            "request": request,
            "coach": coach,
            "clases": clases
        }
    )

@router.get("/{id_coach}/clases")
def gestionar_clases_form(request: Request, id_coach: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Coach
    cursor.execute(
        "SELECT * FROM coach WHERE id_coach = %s",
        (id_coach,)
    )
    coach = cursor.fetchone()

    if not coach:
        cursor.close()
        conn.close()
        return {"error": "Coach no encontrado"}

    # Todas las clases activas + si están asignadas
    cursor.execute("""
        SELECT 
            c.*,
            CASE 
                WHEN cc.id_coach IS NOT NULL THEN 1
                ELSE 0
            END AS asignada
        FROM clase c
        LEFT JOIN clase_coach cc
            ON c.id_clase = cc.id_clase
            AND cc.id_coach = %s
        WHERE c.activo = TRUE
        ORDER BY c.nombre
    """, (id_coach,))

    clases = cursor.fetchall()

    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        "coaches/clases.html",
        {
            "request": request,
            "coach": coach,
            "clases": clases
        }
    )

@router.post("/{id_coach}/clases")
def gestionar_clases_post(
    id_coach: int,
    clases: list[int] = Form(default=[])
):
    conn = get_connection()
    cursor = conn.cursor()

    # Quitar todas las clases actuales
    cursor.execute(
        "DELETE FROM clase_coach WHERE id_coach = %s",
        (id_coach,)
    )

    # Insertar las seleccionadas
    for id_clase in clases:
        cursor.execute("""
            INSERT INTO clase_coach (id_clase, id_coach)
            VALUES (%s, %s)
        """, (id_clase, id_coach))

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(
        url=f"/coaches/{id_coach}",
        status_code=303
    )

@router.get("/{id_coach}/editar")
def editar_coach_form(request: Request, id_coach: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM coach WHERE id_coach = %s",
        (id_coach,)
    )
    coach = cursor.fetchone()

    cursor.close()
    conn.close()

    if not coach:
        raise HTTPException(status_code=404, detail="Coach no encontrado")

    return templates.TemplateResponse(
        "coaches/edit.html",
        {
            "request": request,
            "coach": coach
        }
    )


@router.post("/{id_coach}/editar")
def editar_coach_post(
    id_coach: int,
    nombre: str = Form(...),
    telefono: str = Form(None),
    activo: int = Form(...)
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE coach
        SET nombre = %s,
            telefono = %s,
            activo = %s
        WHERE id_coach = %s
    """, (
        nombre,
        telefono,
        activo,
        id_coach
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(
        url="/coaches",
        status_code=303
    )




