"""
Service for financial transactions and reporting.
"""
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database.db import get_db_session
from ..database.models import (
    Gasto, Proveedor, Categoria, MetodoPago, TipoGasto, 
    CatalogoProducto, Inventario
)

logger = logging.getLogger(__name__)

class FinanceService:
    """Service to handle financial transactions."""

    def _get_or_create(self, session: Session, model: Any, name: str) -> Any:
        """Helper to get a record by name or create it if missing."""
        if not name:
            return None
        
        # Case insensitive search
        instance = session.query(model).filter(func.lower(model.nombre) == name.lower()).first()
        if instance:
            return instance
        
        # Create new
        instance = model(nombre=name)
        session.add(instance)
        # Flush to get the ID but not commit yet
        session.flush() 
        return instance

    def register_purchase(self, 
                          product_name: str, 
                          quantity: float, 
                          unit: str, 
                          cost: float, 
                          provider_name: str, 
                          payment_method_name: str) -> Optional[Gasto]:
        """
        Register a purchase of inventory (Ingreso + Gasto).
        Triggers database stock update automatically.
        """
        try:
            with get_db_session() as session:
                # 1. Resolve dependencies
                provider = self._get_or_create(session, Proveedor, provider_name or "Desconocido")
                payment = self._get_or_create(session, MetodoPago, payment_method_name or "Efectivo")
                
                # Check product exists or create it
                product = session.query(CatalogoProducto).filter(
                    func.lower(CatalogoProducto.nombre) == product_name.lower()
                ).first()
                
                if not product:
                    # Default category for new products
                    default_cat = self._get_or_create(session, Categoria, "Insumos")
                    product = CatalogoProducto(
                        nombre=product_name,
                        unidad_medida=unit or "unidad",
                        categoria_id=default_cat.id
                    )
                    session.add(product)
                    session.flush()

                # 2. Create the Expense Record
                gasto = Gasto(
                    monto=cost,
                    fecha_compra=func.now(),
                    proveedor_id=provider.id if provider else None,
                    metodo_pago_id=payment.id if payment else None,
                    producto_id=product.id,
                    cantidad_comprada=quantity,
                    tipo_gasto_id=self._get_or_create(session, TipoGasto, "Variable").id,
                    categoria_id=product.categoria_id,
                    observaciones=f"Compra de {product_name}"
                )
                
                session.add(gasto)
                session.commit()
                
                # Refresh to return full object
                session.refresh(gasto)
                logger.info(f"Registered purchase: {product_name}, Qty: {quantity}, Cost: {cost}")
                return gasto

        except Exception as e:
            logger.error(f"Error registering purchase: {e}")
            return None

    def register_expense(self, 
                         category_name: str, 
                         cost: float, 
                         provider_name: str, 
                         payment_method_name: str) -> Optional[Gasto]:
        """
        Register a fixed expense or service payment (No inventory).
        """
        try:
            with get_db_session() as session:
                provider = self._get_or_create(session, Proveedor, provider_name or "Desconocido")
                payment = self._get_or_create(session, MetodoPago, payment_method_name or "Efectivo")
                category = self._get_or_create(session, Categoria, category_name or "General")
                
                gasto = Gasto(
                    monto=cost,
                    fecha_compra=func.now(),
                    proveedor_id=provider.id,
                    metodo_pago_id=payment.id,
                    categoria_id=category.id,
                    tipo_gasto_id=self._get_or_create(session, TipoGasto, "Fijo").id,
                    observaciones=f"Pago de {category_name}"
                )
                
                session.add(gasto)
                session.commit()
                session.refresh(gasto)
                return gasto

        except Exception as e:
            logger.error(f"Error registering expense: {e}")
            return None

    def get_expenses_by_provider(self, limit: int = 5) -> str:
        """Report: Total expenses by provider."""
        try:
            with get_db_session() as session:
                results = session.query(
                    Proveedor.nombre, 
                    func.sum(Gasto.monto).label('total')
                ).join(Gasto).group_by(Proveedor.nombre).order_by(text('total DESC')).limit(limit).all()
                
                if not results:
                    return "No hay gastos registrados."

                report = "📊 **Gastos por Proveedor:**\n"
                for row in results:
                    report += f"• {row.nombre}: ${row.total:,.0f}\n"
                return report
        except Exception as e:
            logger.error(f"Error generating provider report: {e}")
            return "Error al generar reporte."
