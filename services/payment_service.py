import uuid
import logging
from datetime import date
from sqlalchemy.orm import Session
from models.accounting import Invoice, Receipt, JournalEntry, JournalLine, ChartOfAccount
from models.customer import Customer
from core.signals import app_signals

logger = logging.getLogger(__name__)

class PaymentProcessingService:
    
    @staticmethod
    def process_customer_receipt(session: Session, invoice_id: str, amount: float, payment_method: str, cash_bank_account_id: str = None, notes: str = "", current_user_id: str = None) -> Receipt:
        """Creates a receipt and updates the associated invoice inside a single atomic transaction."""
        try:
            # 1. Lock the invoice for update to prevent concurrent payment conflicts
            invoice = session.query(Invoice).filter_by(id=invoice_id).with_for_update().first()
            if not invoice:
                raise ValueError(f"Invoice ID {invoice_id} not found.")

            if amount <= 0:
                raise ValueError("Payment amount must be greater than zero.")
            if amount > invoice.amount_remaining:
                raise ValueError(f"Payment ({amount}) exceeds the remaining balance ({invoice.amount_remaining}).")

            # 2. Update Invoice Financials
            from decimal import Decimal
            amount_dec = Decimal(str(amount))
            invoice.amount_paid += amount_dec
            invoice.amount_remaining -= amount_dec

            # 3. Update Invoice Status Dynamically
            if invoice.amount_remaining <= 0:
                invoice.status = "Paid"
            else:
                invoice.status = "Partial"

            # 4. Save Receipt Record
            receipt_id = str(uuid.uuid4())
            receipt = Receipt(
                id=receipt_id,
                receipt_number=f"RCT-{uuid.uuid4().hex[:6].upper()}",
                customer_id=invoice.customer_id,
                invoice_id=invoice.id,
                receipt_date=date.today(),
                amount=amount,
                payment_method=payment_method,
                notes=notes,
                created_by=current_user_id
            )
            session.add(receipt)
            
            # 6. Ledger Postings (Debit Bank, Credit AR)
            if cash_bank_account_id:
                ar_account = session.query(ChartOfAccount).filter_by(account_name="Accounts Receivable").first()
                if ar_account:
                    journal_id = str(uuid.uuid4())
                    session.add(JournalEntry(
                        id=journal_id, entry_number=f"JRN-PAY-{uuid.uuid4().hex[:6].upper()}",
                        entry_date=date.today(), entry_type="Receipt", reference_type="Receipt",
                        reference_id=receipt_id, is_posted=True, status="Posted", created_by=current_user_id
                    ))

                    session.add(JournalLine(
                        id=str(uuid.uuid4()), journal_entry_id=journal_id, account_id=cash_bank_account_id,
                        debit_amount=amount, credit_amount=0, created_by=current_user_id
                    ))
                    session.add(JournalLine(
                        id=str(uuid.uuid4()), journal_entry_id=journal_id, account_id=ar_account.id,
                        debit_amount=0, credit_amount=amount, created_by=current_user_id
                    ))

            # 7. Commit Transaction (All or Nothing)
            session.commit()
            
            # 8. Global Signal broadcast to trigger UI updates automatically
            app_signals.payment_received.emit(invoice.id)
            
            logger.info(f"Receipt {receipt.receipt_number} created successfully. Invoice {invoice.invoice_number} updated.")
            return receipt

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to process receipt: {e}")
            raise e
