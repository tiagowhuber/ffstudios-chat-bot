"""
Service functions for managing inventory operations.
"""
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..database.db import get_db_session
from ..database.models import Inventory
from .fuzzy_matcher import FuzzyMatcher


class InventoryService:
    """Service class for inventory operations."""
    
    @staticmethod
    def add_ingredient(
        ingredient_name: str, 
        quantity: float, 
        unit: str
    ) -> Optional[Inventory]:
        """
        Add a new ingredient to the inventory.
        
        Args:
            ingredient_name: Name of the ingredient
            quantity: Quantity of the ingredient
            unit: Unit of measurement (e.g., 'kg', 'liters', 'pcs')
            
        Returns:
            The created Inventory instance, or None if creation failed
            
        Raises:
            ValueError: If input parameters are invalid
            SQLAlchemyError: If database operation fails
        """
        if not ingredient_name or not ingredient_name.strip():
            raise ValueError("El nombre del ingrediente no puede estar vacío")
        
        if quantity < 0:
            raise ValueError("La cantidad no puede ser negativa")
        
        if not unit or not unit.strip():
            raise ValueError("La unidad no puede estar vacía")
        
        try:
            with get_db_session() as session:
                # Check if ingredient already exists
                existing = session.query(Inventory).filter(
                    Inventory.ingredient_name.ilike(ingredient_name.strip())
                ).first()
                
                if existing:
                    raise ValueError(f"El ingrediente '{ingredient_name}' ya existe con ID {existing.id}")
                
                # Create new inventory item
                new_item = Inventory(
                    ingredient_name=ingredient_name.strip(),
                    quantity=Decimal(str(quantity)),
                    unit=unit.strip()
                )
                
                session.add(new_item)
                session.commit()
                session.refresh(new_item)  # Get the auto-generated ID
                
                return new_item
                
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error de base de datos al agregar ingrediente: {str(e)}")
    
    @staticmethod
    def update_quantity(
        ingredient_id: int, 
        new_quantity: float
    ) -> Optional[Inventory]:
        """
        Update the quantity of an existing ingredient.
        
        Args:
            ingredient_id: ID of the ingredient to update
            new_quantity: New quantity value
            
        Returns:
            The updated Inventory instance, or None if not found
            
        Raises:
            ValueError: If input parameters are invalid
            SQLAlchemyError: If database operation fails
        """
        if new_quantity < 0:
            raise ValueError("La cantidad no puede ser negativa")
        
        try:
            with get_db_session() as session:
                item = session.query(Inventory).filter(Inventory.id == ingredient_id).first()
                
                if not item:
                    return None
                
                item.quantity = Decimal(str(new_quantity))
                session.commit()
                session.refresh(item)
                
                return item
                
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error de base de datos al actualizar cantidad: {str(e)}")
    
    @staticmethod
    def add_quantity(
        ingredient_id: int, 
        quantity_to_add: float
    ) -> Optional[Inventory]:
        """
        Add quantity to an existing ingredient (useful for restocking).
        
        Args:
            ingredient_id: ID of the ingredient
            quantity_to_add: Quantity to add to current stock
            
        Returns:
            The updated Inventory instance, or None if not found
            
        Raises:
            ValueError: If input parameters are invalid
            SQLAlchemyError: If database operation fails
        """
        if quantity_to_add <= 0:
            raise ValueError("La cantidad a agregar debe ser positiva")
        
        try:
            with get_db_session() as session:
                item = session.query(Inventory).filter(Inventory.id == ingredient_id).first()
                
                if not item:
                    return None
                
                item.quantity += Decimal(str(quantity_to_add))
                session.commit()
                session.refresh(item)
                
                return item
                
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error de base de datos al agregar cantidad: {str(e)}")
    
    @staticmethod
    def remove_quantity(
        ingredient_id: int, 
        quantity_to_remove: float
    ) -> Optional[Inventory]:
        """
        Remove quantity from an existing ingredient (useful for usage tracking).
        
        Args:
            ingredient_id: ID of the ingredient
            quantity_to_remove: Quantity to remove from current stock
            
        Returns:
            The updated Inventory instance, or None if not found
            
        Raises:
            ValueError: If input parameters are invalid or would result in negative stock
            SQLAlchemyError: If database operation fails
        """
        if quantity_to_remove <= 0:
            raise ValueError("La cantidad a quitar debe ser positiva")
        
        try:
            with get_db_session() as session:
                item = session.query(Inventory).filter(Inventory.id == ingredient_id).first()
                
                if not item:
                    return None
                
                new_quantity = item.quantity - Decimal(str(quantity_to_remove))
                if new_quantity < 0:
                    raise ValueError(f"No se pueden quitar {quantity_to_remove} {item.unit}. Solo hay {item.quantity} {item.unit} disponibles.")
                
                item.quantity = new_quantity
                session.commit()
                session.refresh(item)
                
                return item
                
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error de base de datos al quitar cantidad: {str(e)}")
    
    @staticmethod
    def delete_ingredient(ingredient_id: int) -> bool:
        """
        Delete an ingredient from the inventory.
        
        Args:
            ingredient_id: ID of the ingredient to delete
            
        Returns:
            True if ingredient was deleted, False if not found
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            with get_db_session() as session:
                item = session.query(Inventory).filter(Inventory.id == ingredient_id).first()
                
                if not item:
                    return False
                
                session.delete(item)
                session.commit()
                
                return True
                
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error de base de datos al eliminar ingrediente: {str(e)}")
    
    @staticmethod
    def get_ingredient_by_id(ingredient_id: int) -> Optional[Inventory]:
        """
        Get an ingredient by its ID.
        
        Args:
            ingredient_id: ID of the ingredient
            
        Returns:
            The Inventory instance, or None if not found
        """
        try:
            with get_db_session() as session:
                return session.query(Inventory).filter(Inventory.id == ingredient_id).first()
                
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error de base de datos al obtener ingrediente: {str(e)}")
    
    @staticmethod
    def get_ingredient_by_name(ingredient_name: str) -> Optional[Inventory]:
        """
        Get an ingredient by its name (case-insensitive).
        
        Args:
            ingredient_name: Name of the ingredient
            
        Returns:
            The Inventory instance, or None if not found
        """
        try:
            with get_db_session() as session:
                return session.query(Inventory).filter(
                    Inventory.ingredient_name.ilike(ingredient_name.strip())
                ).first()
                
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error de base de datos al obtener ingrediente: {str(e)}")
    
    @staticmethod
    def get_ingredient_by_name_fuzzy(
        ingredient_name: str, 
        min_similarity: float = 0.7
    ) -> Optional[Tuple[Inventory, float]]:
        """
        Get an ingredient by its name using fuzzy matching for typos.
        
        Args:
            ingredient_name: Name of the ingredient (may contain typos)
            min_similarity: Minimum similarity threshold for fuzzy matching
            
        Returns:
            Tuple of (Inventory instance, similarity_score) or None if not found
        """
        try:
            # First try exact match
            exact_match = InventoryService.get_ingredient_by_name(ingredient_name)
            if exact_match:
                return (exact_match, 1.0)
            
            # If no exact match, try fuzzy matching
            with get_db_session() as session:
                all_ingredients = session.query(Inventory).all()
                
                if not all_ingredients:
                    return None
                
                # Get all ingredient names for fuzzy matching
                ingredient_names = [item.ingredient_name for item in all_ingredients]
                
                # Find best fuzzy match
                best_match = FuzzyMatcher.find_best_match(
                    ingredient_name, 
                    ingredient_names, 
                    min_similarity
                )
                
                if best_match:
                    matched_name, similarity = best_match
                    # Find the inventory item with the matched name
                    matched_item = session.query(Inventory).filter(
                        Inventory.ingredient_name.ilike(matched_name)
                    ).first()
                    
                    if matched_item:
                        return (matched_item, similarity)
                
                return None
                
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error de base de datos al obtener ingrediente con fuzzy matching: {str(e)}")
    
    @staticmethod
    def list_all_ingredients() -> List[Inventory]:
        """
        Get all ingredients in the inventory.
        
        Returns:
            List of all Inventory instances
        """
        try:
            with get_db_session() as session:
                return session.query(Inventory).order_by(Inventory.ingredient_name).all()
                
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error de base de datos al obtener todos los ingredientes: {str(e)}")
    
    @staticmethod
    def search_ingredients(search_term: str) -> List[Inventory]:
        """
        Search for ingredients by name (case-insensitive partial match).
        
        Args:
            search_term: Term to search for in ingredient names
            
        Returns:
            List of matching Inventory instances
        """
        try:
            with get_db_session() as session:
                return session.query(Inventory).filter(
                    Inventory.ingredient_name.ilike(f"%{search_term.strip()}%")
                ).order_by(Inventory.ingredient_name).all()
                
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error de base de datos al buscar ingredientes: {str(e)}")


# Convenience functions for easier use
def add_ingredient(ingredient_name: str, quantity: float, unit: str) -> Optional[Inventory]:
    """Add a new ingredient to the inventory."""
    return InventoryService.add_ingredient(ingredient_name, quantity, unit)


def remove_ingredient(ingredient_id: int) -> bool:
    """Remove an ingredient from the inventory."""
    return InventoryService.delete_ingredient(ingredient_id)


def update_ingredient_quantity(ingredient_id: int, new_quantity: float) -> Optional[Inventory]:
    """Update the quantity of an ingredient."""
    return InventoryService.update_quantity(ingredient_id, new_quantity)


def get_all_ingredients() -> List[Inventory]:
    """Get all ingredients in the inventory."""
    return InventoryService.list_all_ingredients()


def find_ingredient(ingredient_name: str) -> Optional[Inventory]:
    """Find an ingredient by name."""
    return InventoryService.get_ingredient_by_name(ingredient_name)


def find_ingredient_fuzzy(ingredient_name: str, min_similarity: float = 0.7) -> Optional[Tuple[Inventory, float]]:
    """Find an ingredient by name using fuzzy matching for typos."""
    return InventoryService.get_ingredient_by_name_fuzzy(ingredient_name, min_similarity)