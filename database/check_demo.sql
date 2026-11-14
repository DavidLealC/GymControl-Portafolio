-- Consultas de SOLO LECTURA. No muestran nombres, teléfonos, notas médicas ni contraseñas.
-- Ejecútalas en MySQL Workbench tras importar schema_demo.sql y seed_demo.sql.
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'gymcontrol_demo'
ORDER BY TABLE_NAME;

SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'gymcontrol_demo'
  AND (
    (TABLE_NAME = 'cliente' AND COLUMN_NAME IN ('prioridad_manual', 'fecha_registro')) OR
    (TABLE_NAME = 'pago' AND COLUMN_NAME IN ('tipo_pago','visitas_totales','visitas_restantes')) OR
    (TABLE_NAME = 'asistencia_clase' AND COLUMN_NAME = 'id_pago')
  )
ORDER BY TABLE_NAME, ORDINAL_POSITION;

SELECT TABLE_NAME, COUNT(*) AS cantidad_columnas
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'gymcontrol_demo'
GROUP BY TABLE_NAME
ORDER BY TABLE_NAME;
