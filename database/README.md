# Base de datos de demostración de GymControl

## Objetivo

Instalar una base **nueva e independiente**, compatible con las consultas de la última versión local del código, sin publicar datos del gimnasio.

Los archivos están separados deliberadamente:

- `schema_demo.sql`: **solo estructura** de 10 tablas; no crea usuarios ni inserta registros.
- `seed_demo.sql`: datos **totalmente ficticios** para ensayar membresías y paquetes de visitas.
- `check_demo.sql`: consultas de **solo lectura** para verificar tablas y columnas.

**No ejecutes estos scripts sobre `gimnasio_db` ni importes aquí `respaldo.sql` o `respaldo_antes_visitas.sql`.** Los respaldos contienen información real. No forman parte de GitHub.

## Procedencia y límites de lo confirmado

El esquema deriva de las definiciones `CREATE TABLE` de `respaldo.sql`, el último volcado disponible de MySQL 8.4.7. Los volcados contienen registros reales, pero se extrajeron **solamente las definiciones de tablas**. Las dos diferencias introducidas para hacer la instalación compatible con la versión local de `app/routes/clientes.py` son:

1. `cliente.prioridad_manual TINYINT(1) NOT NULL DEFAULT 0`, necesaria para el orden y los botones de enviar al final/restaurar prioridad. **El tipo y el valor predeterminado son decisiones de compatibilidad**, pues esta columna no aparece en los volcados recibidos.
2. Adición de `bimestre`, `trimestre`, `cuatrimestre` al `ENUM pago.tipo_pago`, junto con `dia`, `semana`, `mes`, `anio` y `visitas`, tal como lo exige el código de pagos. Es una **ampliación inferida**, no una estructura observada en el volcado.

`pago.visitas_totales`, `pago.visitas_restantes` y `asistencia_clase.id_pago` **sí** están presentes en el último respaldo.

Por tanto, `schema_demo.sql` es un **esquema reconstruido para instalaciones nuevas**, no una prueba de que el esquema de producción tuviera exactamente todas estas columnas.

## Instalación sin riesgo para la base original

Requiere MySQL **8.0+**. El volcado de referencia procede de MySQL 8.4.7. Recomendación: usa MySQL Workbench con un usuario local dedicado a pruebas.

1. Comprueba que en tu servidor **no exista** una base llamada `gymcontrol_demo`. El script se detiene si ese nombre ya existe; no borra ni reemplaza nada.
2. Ejecuta `schema_demo.sql` desde Workbench; creará `gymcontrol_demo` con las diez tablas y sus claves foráneas.
3. Ejecuta `seed_demo.sql` **solo una vez** si quieres cargar clientes y pagos ficticios. Está pensado para la base recién creada y usa identificadores iniciales.
4. Ejecuta `check_demo.sql` y confirma que aparezcan diez tablas, el campo `prioridad_manual`, los campos de visitas y el `ENUM` ampliado.
5. En un archivo `.env` **local, nunca en Git**, configura `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME=gymcontrol_demo` y `SECRET_KEY`. El código actual lee estas variables en `app/database.py` y `app/main.py`.
6. Crea **manualmente** un usuario administrador local con contraseña hasheada mediante `app/security.py` (`hash_password` usa bcrypt). No hay contraseñas predeterminadas incluidas en el seed. Para obtener el hash sin escribir la contraseña en el historial de la terminal, desde la carpeta raíz del repositorio y con las dependencias de Python instaladas ejecuta:

   ```bash
   python -c "from getpass import getpass; from app.security import hash_password; print(hash_password(getpass('Clave de prueba: ')))"
   ```

   Copia **solo el hash** producido y ejecuta en Workbench, con la base demo seleccionada:

   ```sql
   USE gymcontrol_demo;
   INSERT INTO usuario_sistema (nombre, usuario, password, rol, activo)
   VALUES ('Administrador Demo', 'admin_demo', 'PEGA_AQUI_EL_HASH_BCRYPT', 'admin', 1);
   ```

   No publiques el hash de esa cuenta ni compartas la contraseña. Si copias el SQL de ejemplo literalmente, el login no funcionará hasta sustituir el marcador.
7. Ejecuta la aplicación **solo en tu equipo de pruebas** y recorre la creación de clientes, membresías, descuentos, paquetes de visitas y listado administrativo.

Ejemplo para cargar la estructura por línea de comandos, utilizando una cuenta MySQL de pruebas:

```bash
mysql -u TU_USUARIO_LOCAL -p < database/schema_demo.sql
mysql -u TU_USUARIO_LOCAL -p < database/seed_demo.sql
mysql -u TU_USUARIO_LOCAL -p < database/check_demo.sql
```

> El desarrollador ejecutó `schema_demo.sql` y `seed_demo.sql` en MySQL 8 y confirmó la creación de las diez tablas y las pruebas funcionales con datos ficticios (9 de noviembre de 2026). **Aún faltan pruebas automatizadas de integración con MySQL.**

## Migración de una base existente

**No se entrega una migración automática** porque los volcados disponibles no incluyen todas las columnas utilizadas por el código final, y no sabemos si tu base operativa recibió alteraciones posteriores. Antes de plantearla, solicita una exportación **solo de estructura** (`mysqldump --no-data`), nunca datos personales, y compara `SHOW CREATE TABLE cliente`, `SHOW CREATE TABLE pago` y `SHOW CREATE TABLE asistencia_clase`. Trabaja siempre con una copia aislada y respaldada, no con la base operativa.

## Limitaciones de la aplicación, independientes del esquema

- Las rutas administrativas requieren inicio de sesión; los formularios POST incluyen tokens CSRF por sesión. Sigue pendiente una auditoría más amplia de seguridad y permisos por rol.
- El uso simultáneo de visitas no utiliza bloqueo transaccional en el código original; el esquema no resuelve por sí mismo esa carrera.
- El listado de clientes se corrigió para manejar búsquedas sin resultados sin lanzar `IndexError`.
- La instalación demo fue probada manualmente en MySQL 8. El respaldo histórico puede no reflejar todos los cambios que se hicieron directamente en la base operativa; aún faltan pruebas automatizadas end-to-end.

Estas limitaciones se documentan, sin reescribir en esta rama la lógica que funcionaba en el gimnasio.
