"""
Service for financial transactions and reporting.
"""
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from ..database.db import get_db_session
from ..database.models import (
    Gasto, Proveedor, Categoria, MetodoPago, TipoGasto, 
    CatalogoProducto, Inventario
)
from .fuzzy_matcher import FuzzyMatcher

logger = logging.getLogger(__name__)

class FinanceService:
    """Service to handle financial transactions."""

    def _get_or_create(self, session: Session, model: Any, name: str) -> Any:
        """Helper to get a record by name or create it if missing."""
        if not name:
            return None
        
        # 1. Exact/Case interaction search (fast path)
        instance = session.query(model).filter(func.lower(model.nombre) == name.lower()).first()
        if instance:
            return instance

        # 2. Normalized search (avoids duplicates like Lider vs Líder)
        # Fetch all names to compare in python (assuming small tables)
        all_records = session.query(model).all()
        
        norm_name = FuzzyMatcher.normalize_string(name)
        
        for record in all_records:
            if FuzzyMatcher.normalize_string(record.nombre) == norm_name:
                logger.info(f"Merged '{name}' with existing '{record.nombre}'")
                return record
                
        # 3. Fuzzy search for small typos (high threshold)
        for record in all_records:
            if FuzzyMatcher.is_close_match(name, record.nombre, min_similarity=0.9):
                logger.info(f"Fuzzy matched '{name}' with existing '{record.nombre}'")
                return record
        
        # Create new
        instance = model(nombre=name)
        session.add(instance)
        # Flush to get the ID but not commit yet
        session.flush() 
        return instance

    def _normalize_payment_method(self, name: str) -> str:
        """Helper to map common payment aliases to canonical names."""
        if not name:
            return "Efectivo"
            
        cleaned = name.lower().strip()
        
        # Explicit mappings for common abbreviations/aliases
        if cleaned in ["credito", "crédito", "tc", "tarjeta de credito"]:
            return "Tarjeta de Crédito"
        if cleaned in ["debito", "débito", "td", "tarjeta de debito"]:
            return "Tarjeta de Débito"
        if "transferencia" in cleaned:
            return "Transferencia"
            
        return name

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
                
                payment_name = self._normalize_payment_method(payment_method_name)
                payment = self._get_or_create(session, MetodoPago, payment_name)
                
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
                
                payment_name = self._normalize_payment_method(payment_method_name)
                payment = self._get_or_create(session, MetodoPago, payment_name)
                
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

                report = " **Gastos por Proveedor:**\n"
                for row in results:
                    report += f"• {row.nombre}: ${row.total:,.0f}\n"
                return report
        except Exception as e:
            logger.error(f"Error generating provider report: {e}")
            return "Error al generar reporte."

    def get_expenses_by_category(self, limit: int = 5) -> str:
        """Report: Total expenses by category."""
        try:
            with get_db_session() as session:
                results = session.query(
                    Categoria.nombre,
                    func.sum(Gasto.monto).label('total')
                ).join(Gasto).group_by(Categoria.nombre).order_by(text('total DESC')).limit(limit).all()
                
                if not results:
                    return "No hay gastos registrados."

                report = " **Gastos por Categoría:**\n"
                for row in results:
                    report += f"• {row.nombre}: ${row.total:,.0f}\n"
                return report
        except Exception as e:
            logger.error(f"Error generating category report: {e}")
            return "Error al generar reporte."

    def get_expenses_by_payment_method(self, limit: int = 5) -> str:
        """Report: Total expenses by payment method."""
        try:
            with get_db_session() as session:
                results = session.query(
                    MetodoPago.nombre,
                    func.sum(Gasto.monto).label('total')
                ).join(Gasto).group_by(MetodoPago.nombre).order_by(text('total DESC')).limit(limit).all()
                
                if not results:
                    return "No hay gastos registrados."

                report = " **Gastos por Método de Pago:**\n"
                for row in results:
                    report += f"• {row.nombre}: ${row.total:,.0f}\n"
                return report
        except Exception as e:
            logger.error(f"Error generating payment method report: {e}")
            return "Error al generar reporte."

    def get_expenses_by_type(self, limit: int = 5) -> str:
        """Report: Total expenses by type (Fijo/Variable)."""
        try:
            with get_db_session() as session:
                results = session.query(
                    TipoGasto.nombre,
                    func.sum(Gasto.monto).label('total')
                ).join(Gasto).group_by(TipoGasto.nombre).order_by(text('total DESC')).limit(limit).all()
                
                if not results:
                    return "No hay gastos registrados."

                report = " **Gastos por Tipo:**\n"
                for row in results:
                    report += f"• {row.nombre}: ${row.total:,.0f}\n"
                return report
        except Exception as e:
            logger.error(f"Error generating expense type report: {e}")
            return "Error al generar reporte."

    def get_expenses_by_product(self, limit: int = 10) -> str:
        """Report: Total expenses by product."""
        try:
            with get_db_session() as session:
                results = session.query(
                    CatalogoProducto.nombre,
                    func.sum(Gasto.monto).label('total'),
                    func.sum(Gasto.cantidad_comprada).label('cantidad')
                ).join(Gasto).group_by(CatalogoProducto.nombre).order_by(text('total DESC')).limit(limit).all()
                
                if not results:
                    return "No hay compras de productos registradas."

                report = " **Gastos por Producto:**\n"
                for row in results:
                    report += f"• {row.nombre}: ${row.total:,.0f} ({row.cantidad:,.1f} unidades)\n"
                return report
        except Exception as e:
            logger.error(f"Error generating product report: {e}")
            return "Error al generar reporte."

    def get_recent_transactions(self, limit: int = 10) -> str:
        """Report: List recent transactions with details."""
        try:
            with get_db_session() as session:
                results = session.query(
                    Gasto.fecha_compra,
                    Gasto.monto,
                    Categoria.nombre.label('categoria'),
                    Proveedor.nombre.label('proveedor')
                ).join(Categoria).join(Proveedor).order_by(Gasto.fecha_compra.desc()).limit(limit).all()
                
                if not results:
                    return "No hay gastos registrados."

                report = " **Transacciones Recientes:**\n"
                for row in results:
                    fecha_str = row.fecha_compra.strftime('%d/%m/%Y') if row.fecha_compra else 'N/A'
                    report += f"• {fecha_str} - ${row.monto:,.0f} - {row.categoria} ({row.proveedor})\n"
                return report
        except Exception as e:
            logger.error(f"Error generating recent transactions report: {e}")
            return "Error al generar reporte."

    def get_recent_expenses_for_deletion(self, search_term: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent expenses as objects, optionally filtering by search term."""
        try:
            with get_db_session() as session:
                query = session.query(
                    Gasto.id,
                    Gasto.fecha_compra,
                    Gasto.monto,
                    Gasto.observaciones,
                    Gasto.cantidad_comprada,
                    Categoria.nombre.label('categoria')
                ).join(Categoria)
                
                if search_term:
                    # Case insensitive search in observations or category
                    term = f"%{search_term}%"
                    query = query.filter(
                        (Gasto.observaciones.ilike(term)) | 
                        (Categoria.nombre.ilike(term))
                    )
                
                results = query.order_by(Gasto.fecha_compra.desc()).limit(limit).all()
                
                expenses = []
                for row in results:
                    expenses.append({
                        "id": str(row.id),
                        "date": row.fecha_compra,
                        "amount": row.monto,
                        "description": row.observaciones,
                        "category": row.categoria,
                        "quantity": row.cantidad_comprada
                    })
                return expenses
        except Exception as e:
            logger.error(f"Error getting expenses for deletion: {e}")
            return []

    def delete_expense(self, expense_id: str) -> bool:
        """Delete an expense by ID."""
        try:
            with get_db_session() as session:
                gasto = session.query(Gasto).filter(Gasto.id == expense_id).first()
                if gasto:
                    session.delete(gasto)
                    session.commit()
                    logger.info(f"Deleted expense {expense_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting expense: {e}")
            return False

    def get_total_expenses_summary(self) -> str:
        """Report: Overall expenses summary."""
        try:
            with get_db_session() as session:
                total = session.query(func.sum(Gasto.monto)).scalar() or 0
                count = session.query(func.count(Gasto.id)).scalar() or 0
                
                # Get breakdown by type
                tipo_results = session.query(
                    TipoGasto.nombre,
                    func.sum(Gasto.monto).label('total')
                ).join(Gasto).group_by(TipoGasto.nombre).all()
                
                if count == 0:
                    return "No hay gastos registrados."

                report = " **Resumen de Gastos:**\n"
                report += f"• Total: ${total:,.0f}\n"
                report += f"• Cantidad de transacciones: {count}\n"
                report += f"• Promedio por transacción: ${total/count:,.0f}\n\n"
                
                if tipo_results:
                    report += "**Por Tipo:**\n"
                    for row in tipo_results:
                        pct = (row.total / total * 100) if total > 0 else 0
                        report += f"• {row.nombre}: ${row.total:,.0f} ({pct:.1f}%)\n"
                
                return report
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
            return "Error al generar reporte."
