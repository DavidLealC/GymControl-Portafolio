from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from app.database import get_connection
from datetime import date
import datetime
from fastapi import Depends
from app.deps import login_required

router = APIRouter(prefix="/historial", tags=["Historial"], dependencies=[Depends(login_required)])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", dependencies=[Depends(login_required)])
def listar_clientes(
    request: Request,
    search: str = "",
    page: int = 1
):
    limit = 20
    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # TOTAL DE REGISTROS (para saber cuántas páginas hay)
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM pago p
        JOIN cliente c ON c.id_cliente = p.id_cliente
        WHERE c.nombre_completo LIKE %s
    """, (f"%{search}%",))
    total = cursor.fetchone()["total"]
    total_pages = (total + limit - 1) // limit

    # REGISTROS DE LA PÁGINA ACTUAL
    cursor.execute("""
    SELECT
    c.id_cliente,
    c.nombre_completo,
    c.telefono,

    p.id_pago,
    p.fecha_pago,
    p.fecha_corte,
    p.tipo_pago,
    p.monto_base,
    p.descuento,
    p.monto_final,

    p.visitas_totales,
    p.visitas_restantes,

    s.nombre AS servicio,
    cl.nombre AS clase,

    CASE
        WHEN p.id_servicio IS NOT NULL THEN 'servicio'
        WHEN p.id_clase IS NOT NULL THEN 'clase'
    END AS tipo_concepto

    FROM pago p
    JOIN cliente c ON c.id_cliente = p.id_cliente
    LEFT JOIN servicio s ON s.id_servicio = p.id_servicio
    LEFT JOIN clase cl ON cl.id_clase = p.id_clase

    WHERE c.nombre_completo LIKE %s
    ORDER BY p.fecha_pago DESC
    LIMIT %s OFFSET %s
    """, (f"%{search}%", limit, offset))

    rows = cursor.fetchall()

    hoy = date.today()
    for r in rows:
        r["vigente"] = r["fecha_corte"] and r["fecha_corte"] >= hoy
        if r["monto_base"] and r["descuento"]:
            r["descuento_pct"] = round(
                (r["descuento"] / r["monto_base"]) * 100, 1
            )
        else:
            r["descuento_pct"] = 0

    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        "historial/list.html",
        {
            "request": request,
            "clientes": rows,
            "search": search,
            "today": hoy,
            "page": page,
            "total_pages": total_pages
        }
    )
