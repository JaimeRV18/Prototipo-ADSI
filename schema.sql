-- schema.sql (Para SQL Server) - VERSIÓN DEFINITIVA
IF DB_ID('SistemaPrestamos') IS NULL
    CREATE DATABASE SistemaPrestamos;
GO
USE SistemaPrestamos;
GO

-- Borrar tablas si existen (para poder correrlo varias veces sin errores)
IF OBJECT_ID('prestamo_componentes', 'U') IS NOT NULL DROP TABLE prestamo_componentes;
IF OBJECT_ID('detalle_solicitud', 'U') IS NOT NULL DROP TABLE detalle_solicitud;
IF OBJECT_ID('solicitud_componentes', 'U') IS NOT NULL DROP TABLE solicitud_componentes;
IF OBJECT_ID('componente', 'U') IS NOT NULL DROP TABLE componente;
IF OBJECT_ID('prestamo_cubiculo', 'U') IS NOT NULL DROP TABLE prestamo_cubiculo;
IF OBJECT_ID('solicitud_cubiculo', 'U') IS NOT NULL DROP TABLE solicitud_cubiculo;
IF OBJECT_ID('cubiculo', 'U') IS NOT NULL DROP TABLE cubiculo;
IF OBJECT_ID('usuario', 'U') IS NOT NULL DROP TABLE usuario;
IF OBJECT_ID('docente', 'U') IS NOT NULL DROP TABLE docente;
IF OBJECT_ID('alumno', 'U') IS NOT NULL DROP TABLE alumno;
IF OBJECT_ID('centro_acopio', 'U') IS NOT NULL DROP TABLE centro_acopio;
GO

CREATE TABLE centro_acopio (
    id        INT IDENTITY(1,1) PRIMARY KEY,
    nombre    NVARCHAR(100) NOT NULL,
    ubicacion NVARCHAR(200) NOT NULL
);

CREATE TABLE alumno (
    matricula NVARCHAR(20) PRIMARY KEY,
    nombre    NVARCHAR(100) NOT NULL,
    carrera   NVARCHAR(100) NOT NULL,
    correo    NVARCHAR(100),
    contrasena NVARCHAR(100) NULL -- NUEVO CAMPO
);

CREATE TABLE docente (
    clave  NVARCHAR(20) PRIMARY KEY,
    nombre NVARCHAR(100) NOT NULL,
    correo NVARCHAR(100),
    contrasena NVARCHAR(100) NULL -- NUEVO CAMPO
);

CREATE TABLE usuario (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    nombre          NVARCHAR(100) NOT NULL,
    usuario         NVARCHAR(50) NOT NULL UNIQUE,
    contrasena_hash NVARCHAR(255) NOT NULL,
    rol             NVARCHAR(20) NOT NULL CHECK (rol IN ('administrador', 'encargado')),
    centro_id       INT NULL REFERENCES centro_acopio(id),
    contrasena      NVARCHAR(100) NULL -- NUEVO CAMPO
);

CREATE TABLE cubiculo (
    id            INT IDENTITY(1,1) PRIMARY KEY,
    numero        NVARCHAR(10) NOT NULL,
    piso          INT NOT NULL,
    lado          NVARCHAR(10) NOT NULL CHECK (lado IN ('izquierdo', 'derecho')),
    docente_clave NVARCHAR(20) NULL REFERENCES docente(clave),
    UNIQUE (piso, numero)
);

CREATE TABLE solicitud_cubiculo (
    id               INT IDENTITY(1,1) PRIMARY KEY,
    alumno_matricula NVARCHAR(20) NOT NULL REFERENCES alumno(matricula),
    cubiculo_id      INT NOT NULL REFERENCES cubiculo(id),
    fecha            NVARCHAR(10) NOT NULL,
    hora_inicio      NVARCHAR(5) NOT NULL,
    hora_fin         NVARCHAR(5) NOT NULL,
    estado           NVARCHAR(20) NOT NULL DEFAULT 'pendiente'
                     CHECK (estado IN ('pendiente', 'autorizada', 'rechazada', 'cancelada', 'finalizada')), -- AGREGADO FINALIZADA
    motivo_rechazo   NVARCHAR(255) NULL,
    resuelta_por     INT NULL REFERENCES usuario(id),
    creada_en        NVARCHAR(30) NOT NULL
);

CREATE TABLE prestamo_cubiculo (
    id           INT IDENTITY(1,1) PRIMARY KEY,
    solicitud_id INT NOT NULL UNIQUE REFERENCES solicitud_cubiculo(id),
    hora_entrada NVARCHAR(5) NULL,
    hora_salida  NVARCHAR(5) NULL
);

CREATE TABLE componente (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    codigo              NVARCHAR(20) NOT NULL UNIQUE,
    nombre              NVARCHAR(100) NOT NULL,
    descripcion         NVARCHAR(255) NULL,
    cantidad_total      INT NOT NULL CHECK (cantidad_total >= 0),
    cantidad_disponible INT NOT NULL CHECK (cantidad_disponible >= 0),
    centro_id           INT NOT NULL REFERENCES centro_acopio(id)
);

CREATE TABLE solicitud_componentes (
    id               INT IDENTITY(1,1) PRIMARY KEY,
    alumno_matricula NVARCHAR(20) NOT NULL REFERENCES alumno(matricula),
    centro_id        INT NOT NULL REFERENCES centro_acopio(id),
    fecha            NVARCHAR(10) NOT NULL,
    estado           NVARCHAR(20) NOT NULL DEFAULT 'pendiente'
                     CHECK (estado IN ('pendiente', 'autorizada', 'rechazada', 'entregada', 'devuelta', 'cancelada')),
    motivo_rechazo   NVARCHAR(255) NULL,
    resuelta_por     INT NULL REFERENCES usuario(id)
);

CREATE TABLE detalle_solicitud (
    id               INT IDENTITY(1,1) PRIMARY KEY,
    solicitud_id     INT NOT NULL REFERENCES solicitud_componentes(id),
    componente_id    INT NOT NULL REFERENCES componente(id),
    cantidad         INT NOT NULL CHECK (cantidad > 0),
    cantidad_perdida INT NOT NULL DEFAULT 0
);

CREATE TABLE prestamo_componentes (
    id               INT IDENTITY(1,1) PRIMARY KEY,
    solicitud_id     INT NOT NULL UNIQUE REFERENCES solicitud_componentes(id),
    fecha_prestamo   NVARCHAR(10) NOT NULL,
    fecha_limite     NVARCHAR(10) NOT NULL,
    fecha_devolucion NVARCHAR(10) NULL,
    entregado_por    INT NULL REFERENCES usuario(id),
    observaciones    NVARCHAR(255) NULL
);
GO