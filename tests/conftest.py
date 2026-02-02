import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, TipoGasto, Categoria, MetodoPago, Proveedor
from src.database.db import get_engine

@pytest.fixture(scope="session")
def engine():
    # Helper to get the engine (assuming DB is set up)
    return get_engine()

@pytest.fixture(scope="function")
def db_session(engine):
    """
    Creates a new database session for a test.
    Rolls back transaction at the end to keep DB clean.
    """
    connection = engine.connect()
    transaction = connection.begin()
    
    Session = sessionmaker(bind=connection)
    session = Session()
    
    # Patch get_db_session to use this session? 
    # Hard to patch the context manager used inside services without more complex mocking.
    # Ideally services accept a session or we rely on 'db.SessionLocal' being patched.
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def seed_data(db_session):
    """Pre-populate lookup tables."""
    # Tipos
    tipos = ["Fijo", "Variable", "Ajuste"]
    for t in tipos:
        if not db_session.query(TipoGasto).filter_by(nombre=t).first():
            db_session.add(TipoGasto(nombre=t))
            
    # Methods
    methods = ["Efectivo", "Débito", "Transferencia"]
    for m in methods:
        if not db_session.query(MetodoPago).filter_by(nombre=m).first():
            db_session.add(MetodoPago(nombre=m))
            
    db_session.commit()
