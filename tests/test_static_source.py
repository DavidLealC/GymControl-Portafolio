import ast
from pathlib import Path
import unittest
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]

class StaticChecks(unittest.TestCase):
    def test_python_syntax(self):
        for path in (ROOT / "app").rglob("*.py"):
            with self.subTest(file=path.name):
                ast.parse(path.read_text(encoding="utf-8-sig"))

    def test_jinja_templates(self):
        root = ROOT / "app" / "templates"
        env = Environment(loader=FileSystemLoader(str(root)))
        for path in root.rglob("*.html"):
            with self.subTest(file=str(path.relative_to(root))):
                env.get_template(path.relative_to(root).as_posix())

    def test_admin_routes_require_login(self):
        directory = ROOT / "app" / "routes"
        for module in ("coaches", "servicios", "descuentos", "historial"):
            with self.subTest(module=module):
                source = (directory / f"{module}.py").read_text(encoding="utf-8-sig")
                declaration = next(line for line in source.splitlines()
                                   if line.startswith("router = APIRouter("))
                self.assertIn("dependencies=[Depends(login_required)]", declaration)

if __name__ == "__main__":
    unittest.main()
