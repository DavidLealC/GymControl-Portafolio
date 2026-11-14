-- GymControl: instalación de DEMOSTRACIÓN sin información real.
-- Fuente: estructura de respaldo.sql (MySQL 8.4.7), SIN sus INSERT de datos reales.
-- Adaptaciones sustentadas en app/routes/clientes.py:
--   * cliente.prioridad_manual  (ORDER BY/UPDATE de clientes)
--   * pago.tipo_pago incluye bimestre, trimestre y cuatrimestre
-- La tabla asistencia_clase incluye id_pago, según respaldo.sql.
-- Requiere MySQL 8.0+ (collation utf8mb4_0900_ai_ci).
-- SEGURIDAD: solo crea gymcontrol_demo; no apuntar a gimnasio_db ni producción.
-- Usa CREATE DATABASE sin IF NOT EXISTS para evitar reusar una base previa.

CREATE DATABASE `gymcontrol_demo` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `gymcontrol_demo`;

CREATE TABLE `cliente` (

  `id_cliente` int NOT NULL AUTO_INCREMENT,
  `nombre_completo` varchar(150) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `telefono_emergencia` varchar(20) DEFAULT NULL,
  `nota_medica` text,
  `estado` tinyint(1) DEFAULT '1',
  `fecha_registro` date NOT NULL,
  `prioridad_manual` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_cliente`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `servicio` (

  `id_servicio` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text,
  `incluye_pesas` tinyint(1) DEFAULT '0',
  `incluye_clase_diaria` tinyint(1) DEFAULT '0',
  `activo` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id_servicio`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `clase` (

  `id_clase` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text,
  `activo` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id_clase`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `coach` (

  `id_coach` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(150) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id_coach`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `descuento` (

  `id_descuento` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `porcentaje` decimal(5,2) NOT NULL,
  `activo` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id_descuento`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `horario` (

  `id_horario` int NOT NULL AUTO_INCREMENT,
  `dia_semana` enum('Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo') NOT NULL,
  `hora_inicio` time NOT NULL,
  `hora_fin` time NOT NULL,
  `id_clase` int NOT NULL,
  `activo` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id_horario`),
  KEY `id_clase` (`id_clase`),
  CONSTRAINT `horario_ibfk_1` FOREIGN KEY (`id_clase`) REFERENCES `clase` (`id_clase`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `clase_coach` (

  `id_clase` int NOT NULL,
  `id_coach` int NOT NULL,
  PRIMARY KEY (`id_clase`,`id_coach`),
  KEY `id_coach` (`id_coach`),
  CONSTRAINT `clase_coach_ibfk_1` FOREIGN KEY (`id_clase`) REFERENCES `clase` (`id_clase`),
  CONSTRAINT `clase_coach_ibfk_2` FOREIGN KEY (`id_coach`) REFERENCES `coach` (`id_coach`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `pago` (

  `id_pago` int NOT NULL AUTO_INCREMENT,
  `fecha_pago` date NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_corte` date NOT NULL,
  `monto_base` decimal(10,2) NOT NULL,
  `descuento` decimal(10,2) DEFAULT '0.00',
  `monto_final` decimal(10,2) NOT NULL,
  `tipo_pago` enum('dia','semana','mes','bimestre','trimestre','cuatrimestre','anio','visitas') NOT NULL,
  `id_cliente` int NOT NULL,
  `id_servicio` int DEFAULT NULL,
  `id_clase` int DEFAULT NULL,
  `id_descuento` int DEFAULT NULL,
  `visitas_totales` int DEFAULT NULL,
  `visitas_restantes` int DEFAULT NULL,
  PRIMARY KEY (`id_pago`),
  KEY `id_cliente` (`id_cliente`),
  KEY `id_servicio` (`id_servicio`),
  KEY `id_clase` (`id_clase`),
  KEY `id_descuento` (`id_descuento`),
  CONSTRAINT `pago_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `cliente` (`id_cliente`),
  CONSTRAINT `pago_ibfk_2` FOREIGN KEY (`id_servicio`) REFERENCES `servicio` (`id_servicio`),
  CONSTRAINT `pago_ibfk_3` FOREIGN KEY (`id_clase`) REFERENCES `clase` (`id_clase`),
  CONSTRAINT `pago_ibfk_4` FOREIGN KEY (`id_descuento`) REFERENCES `descuento` (`id_descuento`),
  CONSTRAINT `chk_pago_tipo` CHECK ((((`id_servicio` is not null) and (`id_clase` is null)) or ((`id_servicio` is null) and (`id_clase` is not null))))

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `asistencia_clase` (

  `id_asistencia` int NOT NULL AUTO_INCREMENT,
  `fecha` date NOT NULL,
  `es_gratis` tinyint(1) DEFAULT '0',
  `id_cliente` int NOT NULL,
  `id_clase` int NOT NULL,
  `id_horario` int NOT NULL,
  `id_pago` int DEFAULT NULL,
  PRIMARY KEY (`id_asistencia`),
  KEY `id_cliente` (`id_cliente`),
  KEY `id_clase` (`id_clase`),
  KEY `id_horario` (`id_horario`),
  KEY `id_pago` (`id_pago`),
  CONSTRAINT `asistencia_clase_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `cliente` (`id_cliente`),
  CONSTRAINT `asistencia_clase_ibfk_2` FOREIGN KEY (`id_clase`) REFERENCES `clase` (`id_clase`),
  CONSTRAINT `asistencia_clase_ibfk_3` FOREIGN KEY (`id_horario`) REFERENCES `horario` (`id_horario`),
  CONSTRAINT `asistencia_clase_ibfk_4` FOREIGN KEY (`id_pago`) REFERENCES `pago` (`id_pago`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `usuario_sistema` (

  `id_usuario` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(150) NOT NULL,
  `usuario` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `rol` varchar(50) DEFAULT 'admin',
  `activo` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `usuario` (`usuario`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

