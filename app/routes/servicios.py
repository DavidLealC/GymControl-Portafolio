from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database import get_connection
from fastapi import HTTPException
from datetime import date
from fastapi import Depends
from app.deps import login_required

router = APIRouter(prefix="/servicios", tags=["Servicios"], dependencies=[Depends(login_required)])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", dependencies=[Depends(login_required)])
def listar_servicios(request: Request):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM servicio
        ORDER BY activo DESC, nombre
    """)
    servicios = cursor.fetchall()

    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        "servicios/list.html",
        {
            "request": request,
            "servicios": servicios
        }
    )


# =========================
# FORMULARIO NUEVO SERVICIO
# =========================
@router.get("/crear")
def crear_servicio_form(request: Request):
    return templates.TemplateResponse(
        "servicios/crear.html",
        {"request": request}
    )


# =========================
# PROCESAR CREACIÓN DE SERVICIO
# =========================
@router.post("/crear")
def crear_servicio_post(
    nombre: str = Form(...),
    descripcion: str = Form(None),
    incluye_pesas: bool = Form(False),
    incluye_clase_diaria: bool = Form(False)
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO servicio (nombre, descripcion, incluye_pesas, incluye_clase_diaria)
        VALUES (%s, %s, %s, %s)
    """, (nombre, descripcion, incluye_pesas, incluye_clase_diaria))

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse("/servicios", status_code=303)


@router.post("/toggle/{id_servicio}")
def toggle_servicio(id_servicio: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # 1️⃣ Ver si el servicio está activo
    cursor.execute("""
        SELECT activo
        FROM servicio
        WHERE id_servicio = %s
    """, (id_servicio,))
    servicio = cursor.fetchone()

    if not servicio:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    # 2️⃣ Si está activo, verificar pagos vigentes
    if servicio["activo"]:
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM pago
            WHERE id_servicio = %s
              AND fecha_corte >= CURDATE()
        """, (id_servicio,))
        activos = cursor.fetchone()["total"]

        if activos > 0:
            cursor.close()
            conn.close()
            # 🚫 NO se permite desactivar
            return RedirectResponse(
                "/servicios?error=servicio_con_pagos_activos",
                status_code=303
            )

    # 3️⃣ Toggle permitido
    cursor.execute("""
        UPDATE servicio
        SET activo = NOT activo
        WHERE id_servicio = %s
    """, (id_servicio,))

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse("/servicios", status_code=303)

@router.get("/editar/{id_servicio}")
def editar_servicio_form(request: Request, id_servicio: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtener servicio
    cursor.execute("SELECT * FROM servicio WHERE id_servicio = %s", (id_servicio,))
    servicio = cursor.fetchone()
    if not servicio:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        "servicios/edit.html",
        {
            "request": request,
            "servicio": servicio
        }
    )

@router.post("/editar/{id_servicio}")
def editar_servicio_post(
    id_servicio: int,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    incluye_pesas: bool = Form(False),
    incluye_clase_diaria: bool = Form(False)
):
    conn = get_connection()
    cursor = conn.cursor()

    # Actualizar datos
    cursor.execute("""
        UPDATE servicio
        SET nombre=%s, descripcion=%s, incluye_pesas=%s, incluye_clase_diaria=%s
        WHERE id_servicio=%s
    """, (nombre, descripcion, incluye_pesas, incluye_clase_diaria, id_servicio))

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(f"/servicios", status_code=303)

