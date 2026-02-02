"""
SQLAlchemy models for the application based on the new schema.
"""
from datetime import datetime
import uuid
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Numeric, DateTime, text, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

# Create the base class for all models
Base = declarative_base()


class TipoGasto(Base):
    __tablename__ = 'tipos_gasto'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(20), nullable=False, unique=True)
    
    gastos = relationship("Gasto", back_populates="tipo_gasto")

    def __repr__(self):
        return f"<TipoGasto(nombre='{self.nombre}')>"


class Categoria(Base):
    __tablename__ = 'categorias'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(Text)
    
    productos = relationship("CatalogoProducto", back_populates="categoria")
    gastos = relationship("Gasto", back_populates="categoria")

    def __repr__(self):
        return f"<Categoria(nombre='{self.nombre}')>"


class MetodoPago(Base):
    __tablename__ = 'metodos_pago'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False, unique=True)
    
    gastos = relationship("Gasto", back_populates="metodo_pago")

    def __repr__(self):
        return f"<MetodoPago(nombre='{self.nombre}')>"


class Proveedor(Base):
    __tablename__ = 'proveedores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True)
    
    gastos = relationship("Gasto", back_populates="proveedor")

    def __repr__(self):
        return f"<Proveedor(nombre='{self.nombre}')>"


class CatalogoProducto(Base):
    __tablename__ = 'catalogo_productos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True)
    unidad_medida = Column(String(20), nullable=False)
    stock_minimo = Column(Numeric(10, 2), server_default=text('5.00'))
    categoria_id = Column(Integer, ForeignKey('categorias.id'))
    
    categoria = relationship("Categoria", back_populates="productos")
    inventario = relationship("Inventario", uselist=False, back_populates="producto", cascade="all, delete-orphan")
    gastos = relationship("Gasto", back_populates="producto")
    salidas = relationship("SalidaInventario", back_populates="producto")

    def __repr__(self):
        return f"<CatalogoProducto(nombre='{self.nombre}')>"


class Inventario(Base):
    __tablename__ = 'inventario'
    
    producto_id = Column(Integer, ForeignKey('catalogo_productos.id'), primary_key=True)
    cantidad_actual = Column(Numeric(12, 2), nullable=False, server_default=text('0.00'))
    ultima_actualizacion = Column(DateTime, default=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP'))
    
    producto = relationship("CatalogoProducto", back_populates="inventario")

    def __repr__(self):
        return f"<Inventario(producto='{self.producto_id}', cantidad={self.cantidad_actual})>"

    @property
    def ingredient_name(self):
        """Helper for compatibility with old code logic"""
        return self.producto.nombre if self.producto else None
        
    @property
    def unit(self):
        """Helper for compatibility with old code logic"""
        return self.producto.unidad_medida if self.producto else None

    @property
    def quantity(self):
        return self.cantidad_actual

    @property
    def last_updated(self):
        return self.ultima_actualizacion


class Gasto(Base):
    __tablename__ = 'gastos'
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    fecha_compra = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP'))
    monto = Column(Numeric(12, 2), nullable=False)
    
    metodo_pago_id = Column(Integer, ForeignKey('metodos_pago.id'))
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'))
    tipo_gasto_id = Column(Integer, ForeignKey('tipos_gasto.id'))
    categoria_id = Column(Integer, ForeignKey('categorias.id'))
    
    # Optional inventory relation
    producto_id = Column(Integer, ForeignKey('catalogo_productos.id'), nullable=True)
    cantidad_comprada = Column(Numeric(10, 2), nullable=True)
    
    item_descripcion = Column(String(255), nullable=True)
    observaciones = Column(Text, nullable=True)
    
    # Relationships
    metodo_pago = relationship("MetodoPago", back_populates="gastos")
    proveedor = relationship("Proveedor", back_populates="gastos")
    tipo_gasto = relationship("TipoGasto", back_populates="gastos")
    categoria = relationship("Categoria", back_populates="gastos")
    producto = relationship("CatalogoProducto", back_populates="gastos")

    def __repr__(self):
        return f"<Gasto(monto={self.monto}, fecha='{self.fecha_compra}')>"


class SalidaInventario(Base):
    __tablename__ = 'salidas_inventario'
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP'))
    producto_id = Column(Integer, ForeignKey('catalogo_productos.id'), nullable=False)
    cantidad_usada = Column(Numeric(10, 2), nullable=False)
    motivo = Column(String(100))
    
    producto = relationship("CatalogoProducto", back_populates="salidas")

    def __repr__(self):
        return f"<SalidaInventario(producto_id={self.producto_id}, cantidad={self.cantidad_usada})>"
