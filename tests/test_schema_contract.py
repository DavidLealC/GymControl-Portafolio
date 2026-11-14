"""Comprobaciones estáticas; no sustituyen levantar MySQL 8."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT / 'database' / 'schema_demo.sql').read_text(encoding='utf-8')
SEED = (ROOT / 'database' / 'seed_demo.sql').read_text(encoding='utf-8')
APP_CLIENTES = (ROOT / 'app' / 'routes' / 'clientes.py').read_text(encoding='utf-8-sig')

class SchemaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = dict(re.findall(
            r'CREATE TABLE `([a-z_]+)` \((.*?)\)\s*ENGINE=InnoDB[^;]*;', SCHEMA, re.S
        ))

    def test_database_is_explicitly_isolated(self):
        self.assertRegex(SCHEMA, r'CREATE DATABASE `gymcontrol_demo`')
        self.assertNotIn('CREATE DATABASE `gimnasio_db`', SCHEMA)
        self.assertNotRegex(SCHEMA, r'(?im)^\s*(?:INSERT|DELETE|UPDATE|DROP|TRUNCATE)\b')

    def test_expected_tables(self):
        self.assertEqual(set(self.tables), {
            'asistencia_clase','clase','clase_coach','cliente','coach',
            'descuento','horario','pago','servicio','usuario_sistema'
        })

    def test_fk_creation_order(self):
        positions = {t:SCHEMA.index('CREATE TABLE `'+t+'`') for t in self.tables}
        for table, body in self.tables.items():
            for referenced in re.findall(r'REFERENCES `([a-z_]+)`',body):
                with self.subTest(table=table, referenced=referenced):
                    self.assertIn(referenced, self.tables)
                    self.assertLess(positions[referenced], positions[table])

    def test_client_priority_column_used_in_code(self):
        self.assertIn('`prioridad_manual` tinyint(1) NOT NULL DEFAULT', self.tables['cliente'])
        self.assertIn('prioridad_manual', APP_CLIENTES)

    def test_visit_columns_and_attendance_relation(self):
        for field in ('visitas_totales','visitas_restantes'):
            self.assertIn('`'+field+'`', self.tables['pago'])
            self.assertIn(field, APP_CLIENTES)
        self.assertIn('`id_pago` int DEFAULT NULL', self.tables['asistencia_clase'])
        self.assertIn('REFERENCES `pago`', self.tables['asistencia_clase'])

    def test_payment_enum_matches_code(self):
        enum = re.search(r'`tipo_pago` enum\((.*?)\)',self.tables['pago'],re.S)
        self.assertIsNotNone(enum)
        accepted = set(re.findall(r"'([^']+)'",enum.group(1)))
        expected = {'dia','semana','mes','bimestre','trimestre','cuatrimestre','anio','visitas'}
        self.assertEqual(accepted, expected)
        for key in expected:
            with self.subTest(period=key):
                self.assertIn('"'+key+'"', APP_CLIENTES)

    def test_only_fictional_seed_data(self):
        self.assertIn('Cliente Demo A', SEED)
        self.assertIn('Cliente Demo B', SEED)
        self.assertIn('Cliente Demo C', SEED)
        self.assertNotRegex(SEED, r'(?im)^\s*(?:DROP|DELETE|UPDATE|ALTER)\b')
        self.assertNotRegex(SEED, r'(?im)^\s*INSERT\s+INTO\s+`?usuario_sistema`?')

if __name__ == '__main__':
    unittest.main()
