import os
import sys
from pathlib import Path

# Ensure the app root is in path
sys.path.insert(0, str(Path.cwd()))

# Load env but force SQLite in-memory for testing
# Load env but force SQLite in-memory for testing
os.environ['USE_SQLITE_FALLBACK'] = 'true'
os.environ['SQLITE_PATH'] = ':memory:'

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.base_model import Base
import models  # Important: import models to ensure they are registered with Base

# For testing, we might need a test session
@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine(os.environ['SQLITE_PATH'])
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="module")
def test_session_factory(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture
def test_session(test_session_factory):
    session = test_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

# Mock get_session for the services to use the test db
@pytest.fixture(autouse=True)
def mock_get_session(monkeypatch, test_session):
    from contextlib import contextmanager
    @contextmanager
    def _mock_get_session():
        yield test_session
        test_session.commit()
    
    import config.database
    monkeypatch.setattr(config.database, "get_session", _mock_get_session)

def test_auth_service(test_session):
    from services.auth_service import AuthService
    from models.user import User
    from utils.encryption import hash_password
    from core.base_model import generate_uuid
    
    # Create test user
    u = User(
        id=generate_uuid(),
        username='testadmin',
        password_hash=hash_password('testpass'),
        full_name='Test Admin',
        role='Admin',
        status='Active'
    )
    test_session.add(u)
    test_session.commit()
    
    auth = AuthService()
    logged_in_user = auth.login('testadmin', 'testpass')
    assert logged_in_user.username == 'testadmin'

def test_customer_service(test_session):
    from services.customer_service import CustomerService
    svc = CustomerService()
    
    # Create customer
    data = {
        'first_name': 'Ali',
        'last_name': 'Khan',
        'phone_primary': '03001234567'
    }
    
    # CustomerService methods might have different signatures
    try:
        customer = svc.create_customer(data, created_by='pytest')
    except TypeError:
        # Some methods just take data
        customer = svc.create_customer(data)
    
    # Retrieve customer
    if isinstance(customer, dict):
        fetched = svc.get_customer_by_id(customer.get('id', ''))
    else:
        fetched = svc.get_customer_by_id(customer.id)
        
    assert fetched is not None
