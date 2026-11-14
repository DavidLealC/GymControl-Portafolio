"""Pruebas de presentación de GymControl sin conectarse a MySQL."""
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader, select_autoescape


TEMPLATES = Path(__file__).resolve().parents[1] / "app" / "templates"
ENV = Environment(
    loader=FileSystemLoader(str(TEMPLATES)),
    autoescape=select_autoescape(["html"]),
)


def render(template, **kwargs):
    context = {
        "request": SimpleNamespace(session={"_csrf_token": "token-de-prueba"}),
        "today": date(2026, 11, 9),
        "page": 1,
        "total_pages": 1,
        "search": "",
    }
    context.update(kwargs)
    return ENV.get_template(template).render(**context)


class PortfolioPresentationTests(unittest.TestCase):
    def test_brand_size_and_semantic_layout(self):
        html = render("base.html")
        self.assertIn('<span class="brand-title">GymControl</span>', html)
        self.assertIn('class="brand-title"', html)
        self.assertIn('name="viewport"', html)
        self.assertIn("<main", html)
        self.assertNotIn('height="360%"', html)
        self.assertNotIn("table-layout: fixed", html)

    def test_client_list_pluralization_and_due_date(self):
        client = {
            "id_cliente": 9, "nombre_completo": "Persona Ficticia",
            "telefono": None, "vigente": True,
            "gym_fecha_corte": date(2026, 11, 10),
            "visitas_restantes": 1,
        }
        html = render("clientes/list.html", clientes=[client])
        self.assertIn("<html", html)
        self.assertIn("1 visita", html)
        self.assertNotIn("1 visitas", html)
        self.assertIn("en 1 día", html)
        self.assertIn("10/11/2026", html)
        self.assertNotIn(">None<", html)

    def test_empty_client_search(self):
        html = render("clientes/list.html", clientes=[], search="sin coincidencias")
        self.assertIn("No encontramos clientes con ese nombre", html)

    def test_visit_payment_is_not_an_expired_membership(self):
        payment = {
            "nombre_completo": "Persona Ficticia", "tipo_pago": "visitas",
            "tipo_concepto": "clase", "servicio": None, "clase": "Yoga",
            "telefono": None, "visitas_totales": 8, "visitas_restantes": 5,
            "monto_base": Decimal("320"), "descuento": Decimal("0"),
            "descuento_pct": 0, "monto_final": Decimal("320"),
            "fecha_pago": date(2026, 11, 4),
            "fecha_corte": date(2026, 11, 4),
            "vigente": False,
        }
        html = render("historial/list.html", clientes=[payment])
        self.assertIn("<html", html)
        self.assertIn("Saldo: 5 / 8", html)
        self.assertIn("Disponible", html)
        self.assertIn("Por visitas", html)
        self.assertNotIn("Vencido", html)
        self.assertNotIn(">None<", html)

        payment["visitas_restantes"] = 0
        depleted = render("historial/list.html", clientes=[payment])
        self.assertIn("Agotado", depleted)

    def test_customer_detail_has_one_priority_action_and_local_dates(self):
        client = {
            "id_cliente": 17, "nombre_completo": "Persona Ficticia",
            "telefono": None, "telefono_emergencia": None,
            "nota_medica": None, "prioridad_manual": 0,
        }
        payment = {
            "tipo_concepto": "servicio", "servicio": "Acceso general",
            "clase": None, "tipo_pago": "mes",
            "fecha_corte": date(2026, 12, 10),
            "fecha_pago": date(2026, 11, 10),
            "monto_final": Decimal("480.00"),
        }
        html = render(
            "clientes/detail.html", cliente=client, pago_actual=payment,
            clases_visitas={"visitas_restantes": 1}, estado_vigente=True,
        )
        self.assertIn("<html", html)
        self.assertIn("Enviar al final", html)
        self.assertNotIn("Restaurar prioridad", html)
        self.assertIn("1 visita restante", html)
        self.assertIn("10/12/2026", html)
        self.assertIn("10/11/2026", html)
        self.assertNotIn(">None<", html)

        client["prioridad_manual"] = 1
        prioritized = render(
            "clientes/detail.html", cliente=client, pago_actual=payment,
            clases_visitas={"visitas_restantes": 1}, estado_vigente=True,
        )
        self.assertIn("Restaurar prioridad", prioritized)
        self.assertNotIn("Enviar al final", prioritized)


if __name__ == "__main__":
    unittest.main()
