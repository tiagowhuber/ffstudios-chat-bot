DROP SCHEMA IF EXISTS public CASCADE;

CREATE SCHEMA IF NOT EXISTS public;

-- Habilitar extensión para UUIDs (si es necesaria)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==========================================
-- 1. TABLAS MAESTRAS
-- ==========================================

CREATE TABLE tipos_gasto (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT
);

CREATE TABLE metodos_pago (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE proveedores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- ==========================================
-- 2. INVENTARIO
-- ==========================================

CREATE TABLE catalogo_productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    unidad_medida VARCHAR(20) NOT NULL,
    stock_minimo DECIMAL(10,2) DEFAULT 5.00,
    categoria_id INT REFERENCES categorias(id)
);

CREATE TABLE inventario (
    producto_id INT PRIMARY KEY REFERENCES catalogo_productos(id),
    cantidad_actual DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 3. TRANSACCIONES (GASTOS Y SALIDAS)
-- ==========================================

CREATE TABLE gastos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fecha_compra TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    monto DECIMAL(12, 2) NOT NULL CHECK (monto > 0),
    
    -- Relaciones
    metodo_pago_id INT REFERENCES metodos_pago(id),
    proveedor_id INT REFERENCES proveedores(id),
    tipo_gasto_id INT REFERENCES tipos_gasto(id),
    categoria_id INT REFERENCES categorias(id),
    
    -- Inventario (Opcional si es servicio)
    producto_id INT REFERENCES catalogo_productos(id),
    cantidad_comprada DECIMAL(10, 2) CHECK (cantidad_comprada > 0),
    item_descripcion VARCHAR(255), -- Usado si producto_id es NULL
    
    observaciones TEXT
);

CREATE TABLE salidas_inventario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    producto_id INT NOT NULL REFERENCES catalogo_productos(id),
    cantidad_usada DECIMAL(10, 2) NOT NULL CHECK (cantidad_usada > 0),
    motivo VARCHAR(100)
);

-- ==========================================
-- 4. TRIGGERS (AUTOMATIZACIÓN STOCK)
-- ==========================================

-- Función para sumar stock al comprar
CREATE OR REPLACE FUNCTION trigger_sumar_stock()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.producto_id IS NOT NULL THEN
        INSERT INTO inventario (producto_id, cantidad_actual, ultima_actualizacion)
        VALUES (NEW.producto_id, NEW.cantidad_comprada, CURRENT_TIMESTAMP)
        ON CONFLICT (producto_id) 
        DO UPDATE SET 
            cantidad_actual = inventario.cantidad_actual + EXCLUDED.cantidad_actual,
            ultima_actualizacion = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_gastos_actualiza_stock
AFTER INSERT ON gastos
FOR EACH ROW
EXECUTE FUNCTION trigger_sumar_stock();

-- Función para restar stock al usar
CREATE OR REPLACE FUNCTION trigger_restar_stock()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE inventario 
    SET cantidad_actual = cantidad_actual - NEW.cantidad_usada,
        ultima_actualizacion = CURRENT_TIMESTAMP
    WHERE producto_id = NEW.producto_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_salidas_actualiza_stock
AFTER INSERT ON salidas_inventario
FOR EACH ROW
EXECUTE FUNCTION trigger_restar_stock();