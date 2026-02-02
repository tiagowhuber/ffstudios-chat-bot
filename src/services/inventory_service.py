"""
Service functions for managing inventory operations using the new schema.
"""
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..database.db import get_db_session
from ..database.models import Inventario, CatalogoProducto, SalidaInventario, Categoria, Gasto, TipoGasto
from .fuzzy_matcher import FuzzyMatcher

class InventoryService:
    """Service class for inventory operations."""
    
    @staticmethod
    def _ensure_product(session: Session, name: str, unit: str) -> CatalogoProducto:
        """Helper to find or create a product definition."""
        name = name.strip()
        product = session.query(CatalogoProducto).filter(
            func.lower(CatalogoProducto.nombre) == name.lower()
        ).first()
        
        if not product:
            # Default category
            cat = session.query(Categoria).filter(Categoria.nombre == "Insumos").first()
            if not cat:
                cat = Categoria(nombre="Insumos")
                session.add(cat)
                session.flush()
                
            product = CatalogoProducto(
                nombre=name,
                unidad_medida=unit,
                categoria_id=cat.id
            )
            session.add(product)
            session.flush() # get ID
            
        return product

    @staticmethod
    def add_ingredient(
        ingredient_name: str, 
        quantity: float, 
        unit: str
    ) -> Optional[Inventario]:
        """
        Add a new ingredient implicitly by making an initial stock adjustment (zero cost purchase).
        """
        try:
            with get_db_session() as session:
                product = InventoryService._ensure_product(session, ingredient_name, unit)
                
                # Check for "Ajuste" Type
                tipo = session.query(TipoGasto).filter(TipoGasto.nombre == "Ajuste").first()
                if not tipo:
                    tipo = TipoGasto(nombre="Ajuste")
                    session.add(tipo)
                    session.flush()
                
                adjustment = Gasto(
                    monto=0,
                    fecha_compra=func.now(),
                    producto_id=product.id,
                    cantidad_comprada=quantity,
                    tipo_gasto_id=tipo.id,
                    observaciones=f"Inventario inicial / Ajuste manual de {ingredient_name}"
                )
                session.add(adjustment)
                session.commit()
                
                # Fetch the result from Inventario table (updated by trigger)
                return session.query(Inventario).filter(Inventario.producto_id == product.id).first()

        except Exception as e:
            raise SQLAlchemyError(f"Error adding ingredient: {e}")

    @staticmethod
    def register_usage(
        ingredient_name: str, 
        quantity: float, 
        reason: str = "Uso diario"
    ) -> Optional[Inventario]:
        """
        Register usage (decrease stock).
        """
        try:
            with get_db_session() as session:
                product = session.query(CatalogoProducto).filter(
                    func.lower(CatalogoProducto.nombre) == ingredient_name.strip().lower()
                ).first()
                
                if not product:
                    raise ValueError(f"Producto '{ingredient_name}' no encontrado.")
                
                # Check stock (optional, trigger might handle negative but good to check)
                inv = session.query(Inventario).filter(Inventario.producto_id == product.id).first()
                current_qty = inv.cantidad_actual if inv else Decimal(0)
                
                if current_qty < Decimal(str(quantity)):
                    raise ValueError(f"Stock insuficiente de {product.nombre}. Actual: {current_qty}")

                # Insert to SalidaInventario -> Trigger updates stock
                salida = SalidaInventario(
                    producto_id=product.id,
                    cantidad_usada=quantity,
                    motivo=reason,
                    fecha=func.now()
                )
                session.add(salida)
                session.commit()
                
                # Refresh inventory to return new state
                # Need to get session again or query fresh? 
                # The session commit should have triggered the specialized update
                # Re-querying is safest
                session.expire_all()
                inv = session.query(Inventario).filter(Inventario.producto_id == product.id).first()
                return inv

        except Exception as e:
            raise SQLAlchemyError(f"Error registering usage: {e}")

    @staticmethod
    def get_ingredient_by_name(ingredient_name: str) -> Optional[Inventario]:
        try:
            with get_db_session() as session:
                return session.query(Inventario).join(CatalogoProducto).filter(
                    func.lower(CatalogoProducto.nombre) == ingredient_name.strip().lower()
                ).first()
        except Exception:
            return None

    @staticmethod
    def get_ingredient_by_name_fuzzy(
        ingredient_name: str, 
        min_similarity: float = 0.7
    ) -> Optional[Tuple[Inventario, float]]:
        try:
            with get_db_session() as session:
                products = session.query(CatalogoProducto).all()
                names = [p.nombre for p in products]
                
                match = FuzzyMatcher.find_best_match(ingredient_name, names, min_similarity)
                if match:
                    name, score = match
                    inv = session.query(Inventario).join(CatalogoProducto).filter(
                        CatalogoProducto.nombre == name
                    ).first()
                    return (inv, score) if inv else None
                return None
        except Exception:
            return None

    @staticmethod
    def list_all_ingredients() -> List[Inventario]:
        with get_db_session() as session:
            return session.query(Inventario).join(CatalogoProducto).order_by(CatalogoProducto.nombre).all()
            
    # Compatibility aliases
    @staticmethod
    def update_quantity(ingredient_id: int, new_quantity: float) -> Optional[Inventario]:
        """Direct stock override (Ajuste)."""
        try:
            with get_db_session() as session:
                inv = session.query(Inventario).filter(Inventario.producto_id == ingredient_id).first()
                if not inv: 
                    return None
                    
                diff = Decimal(str(new_quantity)) - inv.cantidad_actual
                name = inv.ingredient_name
                unit = inv.unit
            
            # Outside session scope to avoid conflicts if calling other methods
            if diff == 0:
                return InventoryService.get_ingredient_by_name(name)
                
            if diff > 0:
                # Add via Gasto (Ajuste)
                return InventoryService.add_ingredient(name, float(diff), unit)
            else:
                # Remove via Salida
                return InventoryService.register_usage(name, float(abs(diff)), "Corrección de stock")
        except Exception as e:
            return None

    @staticmethod
    def remove_quantity(ingredient_id: int, qty: float) -> Optional[Inventario]:
         # Find name first
         with get_db_session() as session:
             inv = session.query(Inventario).get(ingredient_id)
             if not inv: return None
             name = inv.ingredient_name
             
         return InventoryService.register_usage(name, qty)

    @staticmethod
    def add_quantity(ingredient_id: int, qty: float) -> Optional[Inventario]:
         with get_db_session() as session:
             inv = session.query(Inventario).get(ingredient_id)
             if not inv: return None
             name = inv.ingredient_name
             unit = inv.unit
             
         return InventoryService.add_ingredient(name, qty, unit)

# Export simple functions
def find_ingredient(name: str):
    return InventoryService.get_ingredient_by_name(name)

def add_ingredient(name, qty, unit):
    return InventoryService.add_ingredient(name, qty, unit)
