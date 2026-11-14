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

router = APIRouter(prefix="/clientes", tags=["Clientes"], dependencies=[Depends(login_required)])
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
def listar_clientes(request: Request, search: str = "", page: int = 1):

    limit = 20
    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # =========================
    # TOTAL DE REGISTROS
    # =========================
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM cliente
        WHERE nombre_completo LIKE %s
    """, (f"%{search}%",))

    total = cursor.fetchone()["total"]
    total_pages = (total + limit - 1) // limit


    # =========================
    # REGISTROS PAGINADOS
    # =========================
    cursor.execute("""
	SELECT
	    c.id_cliente,
	    c.nombre_completo,
	    c.telefono,
	    c.estado,
	    (
	        SELECT MAX(p.fecha_corte)
	        FROM pago p
	        WHERE p.id_cliente = c.id_cliente
	        AND p.id_servicio IS NOT NULL
	        ORDER BY p.fecha_corte DESC
	        LIMIT 1
	    ) AS gym_fecha_corte,

	    (
	        SELECT COALESCE(SUM(p.visitas_restantes),0)
	        FROM pago p
	        WHERE p.id_cliente = c.id_cliente
	        AND p.tipo_pago='visitas'
	        AND p.visitas_restantes > 0
	    ) AS visitas_restantes

	FROM cliente c
	WHERE c.nombre_completo LIKE %s

	ORDER BY
	prioridad_manual ASC,
	CASE
	    WHEN gym_fecha_corte IS NULL THEN 4
	    WHEN gym_fecha_corte < CURDATE() THEN 1
	    WHEN gym_fecha_corte <= DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN 2
	    ELSE 3
	END,
	gym_fecha_corte ASC

	LIMIT %s OFFSET %s
	""",(f"%{search}%", limit, offset))

    rows = cursor.fetchall()
    hoy = date.today()

    for r in rows:
        r["vigente"] = (
        r["gym_fecha_corte"] and
        r["gym_fecha_corte"] >= hoy
    )

    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        "clientes/list.html",
        {
            "request": request,
            "clientes": rows,
            "search": search,
            "today": hoy,
            "page": page,
            "total_pages": total_pages
        }
    )


# =========================
# CREAR CLIENTE (FORMULARIO)
# =========================
@router.get("/crear")
def crear_cliente_form(request: Request):
    return templates.TemplateResponse(
        "clientes/crear.html",
        {
            "request": request,
            "hoy": date.today()  # por si quieres usarlo como valor por defecto
        }
    )

# =========================
# CREAR CLIENTE (POST)
# =========================
@router.post("/crear")
def crear_cliente_post(
    nombre_completo: str = Form(...),
    telefono: str = Form(""),
    telefono_emergencia: str = Form(""),
    nota_medica: str = Form("")
):
    fecha_registro = date.today()  # fecha de hoy

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cliente (nombre_completo, telefono, telefono_emergencia, nota_medica, fecha_registro)
        VALUES (%s, %s, %s, %s, %s)
    """, (nombre_completo, telefono, telefono_emergencia, nota_medica, fecha_registro))

    conn.commit()
    cursor.close()
    conn.close()

    # Redirige al listado de clientes
    return RedirectResponse(url="/clientes", status_code=303)
# =========================
# DETALLE DEL CLIENTE
# =========================
@router.get("/{id_cliente}")
def detalle_cliente(request: Request, id_cliente: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Cliente
    cursor.execute(
        "SELECT * FROM cliente WHERE id_cliente = %s",
        (id_cliente,)
    )
    cliente = cursor.fetchone()

    if not cliente:
        cursor.close()
        conn.close()
        return {"error": "Cliente no encontrado"}

    # Último pago (servicio o clase)
    cursor.execute("""
        SELECT
            p.*,
            s.nombre AS servicio,
            c.nombre AS clase,
            CASE
                WHEN p.id_servicio IS NOT NULL THEN 'servicio'
                WHEN p.id_clase IS NOT NULL THEN 'clase'
            END AS tipo_concepto
        FROM pago p
        LEFT JOIN servicio s ON s.id_servicio = p.id_servicio
        LEFT JOIN clase c ON c.id_clase = p.id_clase
        WHERE p.id_cliente = %s
        ORDER BY p.fecha_corte DESC
        LIMIT 1
    """, (id_cliente,))
    pago_actual = cursor.fetchone()
    # visitas restantes de clases
    cursor.execute("""
    SELECT COALESCE(SUM(visitas_restantes),0) AS visitas_restantes
    FROM pago
    WHERE id_cliente=%s
    AND tipo_pago='visitas'
    """,(id_cliente,))

    clases_visitas = cursor.fetchone()


    hoy = date.today()
    estado_vigente = pago_actual and pago_actual["fecha_corte"] >= hoy

    # Historial de pagos
    cursor.execute("""
        SELECT
            p.fecha_pago,
            p.tipo_pago,
            p.monto_final,
            s.nombre AS servicio,
            c.nombre AS clase,
            CASE
                WHEN p.id_servicio IS NOT NULL THEN 'servicio'
                WHEN p.id_clase IS NOT NULL THEN 'clase'
            END AS tipo_concepto
        FROM pago p
        LEFT JOIN servicio s ON s.id_servicio = p.id_servicio
        LEFT JOIN clase c ON c.id_clase = p.id_clase
        WHERE p.id_cliente = %s
        ORDER BY p.fecha_pago DESC
    """, (id_cliente,))
    pagos = cursor.fetchall()


    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        "clientes/detail.html",
        {
            "request": request,
            "cliente": cliente,
            "pago_actual": pago_actual,
            "estado_vigente": estado_vigente,
            "pagos": pagos,
            "clases_visitas": clases_visitas
        }
    )


# =========================
# EDITAR CLIENTE (FORM)
# =========================
@router.get("/{id_cliente}/editar")
def editar_cliente_form(request: Request, id_cliente: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM cliente WHERE id_cliente = %s",
        (id_cliente,)
    )
    cliente = cursor.fetchone()

    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        "clientes/edit.html",
        {
            "request": request,
            "cliente": cliente
        }
    )


# =========================
# EDITAR CLIENTE (POST)
# =========================
@router.post("/{id_cliente}/editar")
def editar_cliente_post(
    id_cliente: int,
    nombre_completo: str = Form(...),
    telefono: str = Form(None),
    telefono_emergencia: str = Form(None),
    nota_medica: str = Form(None),
    estado: int = Form(...)
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cliente
        SET
            nombre_completo = %s,
            telefono = %s,
            telefono_emergencia = %s,
            nota_medica = %s,
            estado = %s
        WHERE id_cliente = %s
    """, (
        nombre_completo,
        telefono,
        telefono_emergencia,
        nota_medica,
        estado,
        id_cliente
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(
        url=f"/clientes/{id_cliente}",
        status_code=303
    )

@router.post("/{id_cliente}/mandar-final")
def mandar_final(id_cliente:int):
    conn=get_connection()
    cursor=conn.cursor()

    cursor.execute("""
        UPDATE cliente
        SET prioridad_manual=1
        WHERE id_cliente=%s
    """,(id_cliente,))

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(
        url="/clientes/",
        status_code=303
    )

@router.post("/{id_cliente}/quitar-final")
def quitar_final(id_cliente:int):
    conn=get_connection()
    cursor=conn.cursor()

    cursor.execute("""
        UPDATE cliente
        SET prioridad_manual=0
        WHERE id_cliente=%s
    """,(id_cliente,))

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(
        url="/clientes/",
        status_code=303
    )


@router.get("/{id_cliente}/pago")
def registrar_pago_form(request: Request, id_cliente: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Traer datos del cliente
    cursor.execute(
        "SELECT * FROM cliente WHERE id_cliente = %s",
        (id_cliente,)
    )
    cliente = cursor.fetchone()

    # Traer servicios activos
    cursor.execute(
        "SELECT * FROM servicio WHERE activo = TRUE"
    )
    servicios = cursor.fetchall()
    
    # Traer clases activas
    cursor.execute(
        "SELECT * FROM clase WHERE activo = TRUE"
    )
    clases = cursor.fetchall()

    # Traer descuentos activos
    cursor.execute(
        "SELECT * FROM descuento WHERE activo = TRUE"
    )
    descuentos = cursor.fetchall()

    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        "clientes/pago.html",
        {
            "request": request,
            "cliente": cliente,
            "servicios": servicios,
            "clases": clases,  # agregamos clases
            "descuentos": descuentos,
            "hoy": date.today()
        }
    )


# =========================
# REGISTRAR PAGO (POST)
# =========================
@router.post("/{id_cliente}/pago")
def registrar_pago_post(
    id_cliente: int,
    tipo_pago_objeto: str = Form(...),  # "servicio" o "clase"
    id_servicio: int = Form(None),
    id_clase: int = Form(None),
    tipo_pago: str = Form(...),
    fecha_inicio: date | None = Form(None),
    monto_base: float = Form(...),
    descuento: float = Form(0),
    visitas_totales: int = Form(None)
):
    fecha_pago = date.today()

    # =========================
    # CALCULAR FECHA DE CORTE
    # =========================

    PERIODOS = {
        "dia": timedelta(days=1),
        "semana": timedelta(weeks=1),
        "mes": relativedelta(months=1), 
        "bimestre": relativedelta(months=2), 
        "trimestre": relativedelta(months=3),  
        "cuatrimestre": relativedelta(months=4),    
        "anio": relativedelta(years=1)
    }

    if tipo_pago == "visitas":
        fecha_inicio = fecha_pago
        fecha_corte = fecha_pago
    else:
        fecha_corte = fecha_inicio + PERIODOS.get(
            tipo_pago,
            timedelta(0)
        )


    # =========================
    # CALCULAR MONTO
    # =========================

    monto_final = monto_base - descuento
    visitas_restantes = visitas_totales if tipo_pago == "visitas" else None

    # =========================
    # INSERTAR EN BD
    # =========================

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pago (
            fecha_pago,
            fecha_inicio,
            fecha_corte,
            monto_base,
            descuento,
            monto_final,
            tipo_pago,
            id_cliente,
            id_servicio,
            id_clase,
            visitas_totales,
    	    visitas_restantes
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        fecha_pago,
        fecha_inicio,
        fecha_corte,
        monto_base,
        descuento,
        monto_final,
        tipo_pago,
        id_cliente,
        id_servicio if tipo_pago_objeto == "servicio" else None,
        id_clase if tipo_pago_objeto == "clase" else None,
	visitas_totales if tipo_pago=="visitas" else None,
        visitas_restantes
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(
        url=f"/clientes/{id_cliente}",
        status_code=303
    )

@router.post("/{id_cliente}/usar-visita")
def usar_visita(id_cliente: int):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # buscar el paquete más antiguo con visitas disponibles
    cursor.execute("""
        SELECT id_pago, visitas_restantes
        FROM pago
        WHERE id_cliente=%s
        AND tipo_pago='visitas'
        AND visitas_restantes > 0
        ORDER BY fecha_pago ASC
        LIMIT 1
    """, (id_cliente,))

    pago = cursor.fetchone()

    if pago:
        cursor.execute("""
            UPDATE pago
            SET visitas_restantes = visitas_restantes - 1
            WHERE id_pago=%s
        """,(pago["id_pago"],))

        conn.commit()

    cursor.close()
    conn.close()

    return RedirectResponse(
        url=f"/clientes/{id_cliente}",
        status_code=303
    )
