-- Limpiar datos existentes (opcional, para evitar duplicados si se corre varias veces, aunque los INSERTs pueden fallar por constraints)
-- En este caso usaremos ON CONFLICT DO NOTHING para las tablas catalogo, proveedores, etc.

-- 1. TIPOS DE GASTO
INSERT INTO tipos_gasto (nombre) VALUES 
('Fijo'), 
('Variable') 
ON CONFLICT (nombre) DO NOTHING;

-- 2. CATEGORIAS
INSERT INTO categorias (nombre, descripcion) VALUES 
('Alimentación', 'Gastos de comida e insumos'),
('Servicios Básicos', 'Luz, Agua, Internet'),
('Transporte', 'Bencina, Uber, Metro'),
('Arriendo', 'Pago de alquiler del local'),
('Mantenimiento', 'Reparaciones y limpieza'),
('Sueldos', 'Pago a personal')
ON CONFLICT (nombre) DO NOTHING;

-- 3. METODOS DE PAGO
INSERT INTO metodos_pago (nombre) VALUES 
('Efectivo'),
('Tarjeta de Crédito'),
('Tarjeta de Débito'),
('Transferencia')
ON CONFLICT (nombre) DO NOTHING;

-- 4. PROVEEDORES
INSERT INTO proveedores (nombre) VALUES 
('Lider'),
('Jumbo'),
('Santa Isabel'),
('CGE'),
('Aguas Andinas'),
('VTR'),
('Copec'),
('La Vega Central')
ON CONFLICT (nombre) DO NOTHING;

-- 5. CATALOGO PRODUCTOS
-- Necesitamos IDs de categorias para insertar productos. Asumimos IDs seriales o subqueries.
INSERT INTO catalogo_productos (nombre, unidad_medida, stock_minimo, categoria_id) VALUES 
('Harina', 'kg', 10.00, (SELECT id FROM categorias WHERE nombre = 'Alimentación')),
('Azúcar', 'kg', 5.00, (SELECT id FROM categorias WHERE nombre = 'Alimentación')),
('Leche', 'litro', 10.00, (SELECT id FROM categorias WHERE nombre = 'Alimentación')),
('Huevos', 'unidad', 30.00, (SELECT id FROM categorias WHERE nombre = 'Alimentación')),
('Aceite', 'litro', 5.00, (SELECT id FROM categorias WHERE nombre = 'Alimentación')),
('Chocolate', 'kg', 2.00, (SELECT id FROM categorias WHERE nombre = 'Alimentación'))
ON CONFLICT (nombre) DO NOTHING;

-- 6. GASTOS (Datos históricos y recientes)
-- Función auxiliar para insertar gasto si no existe random ID (o simplemente inserts masivos)
-- Insertamos gastos variados en fechas distintas

-- Gasto 1: Compra grande en Lider (Diciembre 2025)
INSERT INTO gastos (fecha_compra, monto, metodo_pago_id, proveedor_id, tipo_gasto_id, categoria_id, producto_id, cantidad_comprada, observaciones)
VALUES (
    '2025-12-15 10:00:00', 
    45000, 
    (SELECT id FROM metodos_pago WHERE nombre = 'Tarjeta de Crédito'),
    (SELECT id FROM proveedores WHERE nombre = 'Lider'),
    (SELECT id FROM tipos_gasto WHERE nombre = 'Variable'),
    (SELECT id FROM categorias WHERE nombre = 'Alimentación'),
    (SELECT id FROM catalogo_productos WHERE nombre = 'Harina'),
    50,
    'Compra mensual de harina'
);

-- Gasto 2: Luz (Diciembre 2025)
INSERT INTO gastos (fecha_compra, monto, metodo_pago_id, proveedor_id, tipo_gasto_id, categoria_id, observaciones)
VALUES (
    '2025-12-20 15:30:00', 
    35000, 
    (SELECT id FROM metodos_pago WHERE nombre = 'Transferencia'),
    (SELECT id FROM proveedores WHERE nombre = 'CGE'),
    (SELECT id FROM tipos_gasto WHERE nombre = 'Fijo'),
    (SELECT id FROM categorias WHERE nombre = 'Servicios Básicos'),
    'Pago luz diciembre'
);

-- Gasto 3: Compra en Jumbo (Mes pasado: Enero 2026)
INSERT INTO gastos (fecha_compra, monto, metodo_pago_id, proveedor_id, tipo_gasto_id, categoria_id, producto_id, cantidad_comprada, observaciones)
VALUES (
    '2026-01-10 12:00:00', 
    22500, 
    (SELECT id FROM metodos_pago WHERE nombre = 'Tarjeta de Débito'),
    (SELECT id FROM proveedores WHERE nombre = 'Jumbo'),
    (SELECT id FROM tipos_gasto WHERE nombre = 'Variable'),
    (SELECT id FROM categorias WHERE nombre = 'Alimentación'),
    (SELECT id FROM catalogo_productos WHERE nombre = 'Chocolate'),
    5,
    NULL
);

-- Gasto 4: Compra en Lider (Este mes: Febrero 2026 - Semana pasada)
INSERT INTO gastos (fecha_compra, monto, metodo_pago_id, proveedor_id, tipo_gasto_id, categoria_id, producto_id, cantidad_comprada, observaciones)
VALUES (
    CURRENT_DATE - INTERVAL '3 days', 
    15000, 
    (SELECT id FROM metodos_pago WHERE nombre = 'Efectivo'),
    (SELECT id FROM proveedores WHERE nombre = 'Lider'),
    (SELECT id FROM tipos_gasto WHERE nombre = 'Variable'),
    (SELECT id FROM categorias WHERE nombre = 'Alimentación'),
    (SELECT id FROM catalogo_productos WHERE nombre = 'Huevos'),
    60,
    NULL
);

-- Gasto 5: Gasto Fijo Internet (Ayer)
INSERT INTO gastos (fecha_compra, monto, metodo_pago_id, proveedor_id, tipo_gasto_id, categoria_id, observaciones)
VALUES (
    CURRENT_DATE - INTERVAL '1 day', 
    29990, 
    (SELECT id FROM metodos_pago WHERE nombre = 'Tarjeta de Crédito'),
    (SELECT id FROM proveedores WHERE nombre = 'VTR'),
    (SELECT id FROM tipos_gasto WHERE nombre = 'Fijo'),
    (SELECT id FROM categorias WHERE nombre = 'Servicios Básicos'),
    'Internet Fibra'
);
