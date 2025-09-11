"""
SQLAlchemy models for the application.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Integer, String, Numeric, DateTime, text
from sqlalchemy.ext.declarative import declarative_base

# Create the base class for all models
Base = declarative_base()


class Inventory(Base):
    """
    Inventory model representing ingredients and their quantities.
    
    Maps to the 'inventory' table with the following schema:
    CREATE TABLE inventory (
        id SERIAL PRIMARY KEY,
        ingredient_name VARCHAR(100) NOT NULL,
        quantity NUMERIC(10,2) NOT NULL DEFAULT 0,
        unit VARCHAR(20) NOT NULL, -- e.g., 'kg', 'liters', 'pcs'
        last_updated TIMESTAMP DEFAULT NOW()
    );
    """
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ingredient_name = Column(String(100), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=0)
    unit = Column(String(20), nullable=False)  # e.g., 'kg', 'liters', 'pcs'
    last_updated = Column(DateTime, default=datetime.utcnow, server_default=text('NOW()'))
    
    def __repr__(self) -> str:
        return f"<Inventory(id={self.id}, ingredient_name='{self.ingredient_name}', quantity={self.quantity}, unit='{self.unit}')>"
    
    def __str__(self) -> str:
        return f"{self.ingredient_name}: {self.quantity} {self.unit}"
    
    def to_dict(self) -> dict:
        """Convert the model instance to a dictionary."""
        return {
            'id': self.id,
            'ingredient_name': self.ingredient_name,
            'quantity': float(self.quantity) if self.quantity is not None else 0.0,
            'unit': self.unit,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Inventory':
        """Create an Inventory instance from a dictionary."""
        return cls(
            ingredient_name=data.get('ingredient_name'),
            quantity=Decimal(str(data.get('quantity', 0))),
            unit=data.get('unit'),
            last_updated=data.get('last_updated')
        )