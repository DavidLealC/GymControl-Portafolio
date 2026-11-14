-- SOLO DATOS FICTICIOS. Ejecutar DESPUÉS de schema_demo.sql en una base nueva.
-- NO contiene clientes, contraseñas ni registros del gimnasio real.
-- Los IDs de ejemplo suponen tablas recién creadas y sin otros registros.
USE `gymcontrol_demo`;

INSERT INTO `descuento` (`nombre`, `porcentaje`, `activo`) VALUES
('Estudiante - ejemplo', 20.00, 1),
('Promoción - ejemplo', 10.00, 1);

INSERT INTO `servicio` (`nombre`, `descripcion`, `incluye_pesas`, `incluye_clase_diaria`, `activo`) VALUES
('Acceso general - demo', 'Servicio ficticio para demostrar membresías', 1, 0, 1);

INSERT INTO `clase` (`nombre`, `descripcion`, `activo`) VALUES
('Clase de muestra', 'Clase ficticia para demostrar paquetes de visitas', 1);

INSERT INTO `coach` (`nombre`, `telefono`, `activo`) VALUES
('Instructor de demostración', NULL, 1);

INSERT INTO `clase_coach` (`id_clase`, `id_coach`) VALUES (1, 1);

INSERT INTO `horario` (`dia_semana`, `hora_inicio`, `hora_fin`, `id_clase`, `activo`) VALUES
('Lunes', '17:00:00', '18:00:00', 1, 1);

INSERT INTO `cliente` (`nombre_completo`, `telefono`, `telefono_emergencia`, `nota_medica`, `estado`, `fecha_registro`, `prioridad_manual`) VALUES
('Cliente Demo A', NULL, NULL, NULL, 1, CURRENT_DATE(), 0),
('Cliente Demo B', NULL, NULL, NULL, 1, CURRENT_DATE(), 0),
('Cliente Demo C', NULL, NULL, NULL, 1, CURRENT_DATE(), 1);

-- Membresía bimestral ficticia y paquete de ocho visitas con cinco restantes.
INSERT INTO `pago` (
    `fecha_pago`, `fecha_inicio`, `fecha_corte`, `monto_base`, `descuento`, `monto_final`,
    `tipo_pago`, `id_cliente`, `id_servicio`, `id_clase`, `visitas_totales`, `visitas_restantes`
) VALUES
(CURRENT_DATE(), CURRENT_DATE(), DATE_ADD(CURRENT_DATE(), INTERVAL 2 MONTH), 600.00, 0.00, 600.00,
 'bimestre', 1, 1, NULL, NULL, NULL),
(CURRENT_DATE(), CURRENT_DATE(), CURRENT_DATE(), 320.00, 0.00, 320.00,
 'visitas', 2, NULL, 1, 8, 5);

-- No se crea ningún usuario del sistema con contraseña predefinida.
-- Consulta database/README.md para crear un usuario administrador local.
