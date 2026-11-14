"""Checks for the session-based CSRF guard and templates.

These tests deliberately do not connect to MySQL or require credentials.
"""
import ast
import re
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
from jinja2 import Environment, FileSystemLoader
from starlette.middleware.sessions import SessionMiddleware

from app.csrf import csrf_guard

ROOT = Path(__file__).resolve().parents[1]
POST_FORM = re.compile(r"<form\b[^>]*\bmethod\s*=\s*['\"]?post\b[^>]*>", re.I | re.S)
TOKEN_FIELD = 'name="_csrf_token"'


def test_app():
    app = FastAPI(dependencies=[Depends(csrf_guard)])
    app.add_middleware(SessionMiddleware, secret_key="test-only-secret-not-for-production-123456789")

    @app.get("/form")
    def form(request: Request):
        return HTMLResponse(
            f'<form method="post" action="/change">'
            f'<input type="hidden" name="_csrf_token" value="{request.session["_csrf_token"]}">'
            '<input name="value"><button>Guardar</button></form>'
        )

    @app.post("/change")
    def change(value: str = Form(...)):
        return {"saved": value}

    @app.post("/change-json")
    def change_json():
        return {"saved": True}

    return app


class CsrfSecurityTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(test_app())

    def token(self):
        html = self.client.get("/form").text
        found = re.search(r'name="_csrf_token" value="([^\"]+)"', html)
        self.assertIsNotNone(found)
        return found.group(1)

    def test_get_issues_token_and_form_posts_with_it(self):
        token = self.token()
        response = self.client.post("/change", data={"value": "ejemplo", "_csrf_token": token})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"saved": "ejemplo"})

    def test_post_without_token_is_rejected(self):
        self.token()
        response = self.client.post("/change", data={"value": "no autorizado"})
        self.assertEqual(response.status_code, 403)

    def test_wrong_token_is_rejected(self):
        self.token()
        response = self.client.post("/change", data={"value": "no autorizado", "_csrf_token": "wrong"})
        self.assertEqual(response.status_code, 403)

    def test_post_without_session_is_rejected(self):
        response = self.client.post("/change", data={"value": "sin sesión", "_csrf_token": "fake"})
        self.assertEqual(response.status_code, 403)

    def test_json_requires_valid_token_header(self):
        token = self.token()
        self.assertEqual(self.client.post("/change-json", json={}).status_code, 403)
        self.assertEqual(
            self.client.post("/change-json", json={}, headers={"X-CSRF-Token": token}).status_code,
            200,
        )

    def test_all_post_templates_have_token_field(self):
        directory = ROOT / "app" / "templates"
        total = 0
        for path in directory.rglob("*.html"):
            source = path.read_text(encoding="utf-8-sig")
            for match in POST_FORM.finditer(source):
                with self.subTest(template=str(path.relative_to(directory)), offset=match.start()):
                    self.assertIn(TOKEN_FIELD, source[match.end():match.end() + 300])
                    total += 1
        self.assertEqual(total, 20)

    def test_jinja_templates_still_compile(self):
        directory = ROOT / "app" / "templates"
        env = Environment(loader=FileSystemLoader(str(directory)))
        for path in directory.rglob("*.html"):
            with self.subTest(template=path.name):
                env.get_template(path.relative_to(directory).as_posix())

    def test_logout_is_post_only(self):
        route = (ROOT / "app" / "routes" / "login.py").read_text(encoding="utf-8-sig")
        self.assertIn('@router.post("/logout")', route)
        self.assertNotIn('@router.get("/logout")', route)
        self.assertNotIn('href="/logout"', (ROOT / "app" / "templates" / "base.html").read_text(encoding="utf-8-sig"))

    def test_empty_clients_result_does_not_index_first_element(self):
        source = (ROOT / "app" / "routes" / "clientes.py").read_text(encoding="utf-8-sig")
        ast_tree = ast.parse(source)
        function = next(x for x in ast_tree.body if isinstance(x, ast.FunctionDef) and x.name == "listar_clientes")
        function.decorator_list = []
        namespace = {}
        cursor = Mock()
        cursor.fetchone.return_value = {"total": 0}
        cursor.fetchall.return_value = []
        connection = Mock()
        connection.cursor.return_value = cursor
        template_engine = Mock()
        namespace.update({"get_connection": lambda: connection, "date": date, "templates": template_engine, "Request": Request})
        module = ast.Module(body=[function], type_ignores=[])
        exec(compile(module, str(ROOT / "app/routes/clientes.py"), "exec"), namespace)
        result = namespace["listar_clientes"](request=object(), search="sin resultados")
        self.assertEqual(result, template_engine.TemplateResponse.return_value)
        self.assertEqual(template_engine.TemplateResponse.call_args.args[1]["clientes"], [])


if __name__ == "__main__":
    unittest.main()
