import pytest
import uuid
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.base_model import Base
from models.customer import Customer
from models.accounting import Invoice, ChartOfAccount
from services.payment_service import PaymentProcessingService
from core.signals import app_signals

@pytest.fixture
def memory_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_receipt_updates_invoice_db(memory_session):
    # Setup Data
    cust_id = str(uuid.uuid4())
    customer = Customer(id=cust_id, customer_code="CUST-001", first_name="Test", last_name="Customer", phone_primary="1234567890", cnic="12345-1234567-1")
    memory_session.add(customer)

    inv_id = str(uuid.uuid4())
    invoice = Invoice(
        id=inv_id,
        invoice_number="INV-00001",
        customer_id=cust_id,
        issue_date=date.today(),
        subtotal=35000.0,
        total_amount=35000.0,
        amount_paid=0.0,
        amount_remaining=35000.0,
        status="Unpaid"
    )
    memory_session.add(invoice)
    
    acc_id = str(uuid.uuid4())
    ar_acc_id = str(uuid.uuid4())
    cash_acc = ChartOfAccount(id=acc_id, account_code="1001", account_name="Cash", account_type="Asset", opening_balance=0.0)
    ar_acc = ChartOfAccount(id=ar_acc_id, account_code="1002", account_name="Accounts Receivable", account_type="Asset", opening_balance=35000.0)
    memory_session.add(cash_acc)
    memory_session.add(ar_acc)
    
    memory_session.commit()
    
    # Process Receipt
    receipt = PaymentProcessingService.process_customer_receipt(
        session=memory_session,
        invoice_id=inv_id,
        amount=35000.0,
        payment_method="Cash",
        cash_bank_account_id=acc_id,
        notes="Test payment"
    )
    
    # Verify Invoice
    memory_session.refresh(invoice)
    assert invoice.amount_paid == 35000.0
    assert invoice.amount_remaining == 0.0
    assert invoice.status == "Paid"
    


def test_signal_emission(memory_session, qtbot):
    # Ensure signal is emitted
    
    # Mocking
    cust_id = str(uuid.uuid4())
    customer = Customer(id=cust_id, customer_code="CUST-002", first_name="Test", last_name="Customer", phone_primary="1234567890", cnic="12345-1234567-1")
    memory_session.add(customer)

    inv_id = str(uuid.uuid4())
    invoice = Invoice(
        id=inv_id,
        invoice_number="INV-00001",
        customer_id=cust_id,
        issue_date=date.today(),
        subtotal=35000.0,
        total_amount=35000.0,
        amount_paid=0.0,
        amount_remaining=35000.0,
        status="Unpaid"
    )
    memory_session.add(invoice)
    memory_session.commit()
    
    with qtbot.waitSignal(app_signals.payment_received, timeout=1000) as blocker:
        PaymentProcessingService.process_customer_receipt(
            session=memory_session,
            invoice_id=inv_id,
            amount=35000.0,
            payment_method="Cash"
        )
    assert blocker.args[0] == inv_id
