from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.database import get_connection
from fastapi import Depends
from app.deps import login_required

router = APIRouter(prefix="/horarios", tags=["Horarios"])
templates = Jinja2Templates(directory="app/templates")

BLOQUE_MINUTOS = 60  # 👈 CAMBIO AQUÍ

def time_to_minutes(td):
    return td.seconds // 60

def minutes_to_str(m):
    return f"{m//60:02d}:{m%60:02d}"

@router.get("", dependencies=[Depends(login_required)])
def ver_horario_gym(request: Request):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT h.dia_semana, h.hora_inicio, h.hora_fin, c.nombre
        FROM horario h
        JOIN clase c ON h.id_clase = c.id_clase
        WHERE h.activo = TRUE AND c.activo = TRUE
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    dias_semana = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]

    if not rows:
        bloques = []
    else:
        min_h = min(time_to_minutes(r["hora_inicio"]) for r in rows)
        max_h = max(time_to_minutes(r["hora_fin"]) for r in rows)
        bloques = list(range(min_h, max_h, BLOQUE_MINUTOS))

    tabla = {dia: {b: None for b in bloques} for dia in dias_semana}

    for r in rows:
        dia = r["dia_semana"]
        inicio = time_to_minutes(r["hora_inicio"])
        fin = time_to_minutes(r["hora_fin"])

        filas = max(1, (fin - inicio) // BLOQUE_MINUTOS)

        tabla[dia][inicio] = {
            "nombre": r["nombre"],
            "inicio": minutes_to_str(inicio),
            "fin": minutes_to_str(fin),
            "rowspan": filas
        }

        for b in range(
            inicio + BLOQUE_MINUTOS,
            inicio + filas * BLOQUE_MINUTOS,
            BLOQUE_MINUTOS
        ):
            if b in tabla[dia]:
                tabla[dia][b] = "skip"

    return templates.TemplateResponse(
        "horarios/list.html",
        {
            "request": request,
            "dias_semana": dias_semana,
            "bloques": bloques,
            "tabla": tabla
        }
    )
