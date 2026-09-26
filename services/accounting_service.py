import logging
from typing import Optional
from core.base_service import BaseService
from models.accounting import Invoice, InvoiceItem, Receipt, Expense, ChartOfAccount
from repositories.accounting_repository import InvoiceRepository, ReceiptRepository, ExpenseRepository
from core.base_model import generate_uuid
from sqlalchemy import select, or_, func
from datetime import date

logger = logging.getLogger(__name__)
from sqlalchemy.orm import joinedload

class AccountingService(BaseService):
    def search_invoices(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        with self._get_session() as session:
            from models.customer import Customer
            stmt = select(Invoice).options(joinedload(Invoice.customer), joinedload(Invoice.items)).join(Invoice.customer, isouter=True).where(Invoice.is_deleted == False)
            if query:
                stmt = stmt.where(
                    or_(
                        Invoice.invoice_number.ilike(f"%{query}%"),
                        Invoice.status.ilike(f"%{query}%"),
                        Customer.first_name.ilike(f"%{query}%"),
                        Customer.last_name.ilike(f"%{query}%"),
                        Customer.phone_primary.ilike(f"%{query}%"),
                    )
                )
            
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = session.scalar(count_stmt) or 0
            
            stmt = stmt.order_by(Invoice.created_at.desc()).offset(skip).limit(limit)
            items = list(session.scalars(stmt).unique().all())
            return {'items': items, 'total': total, 'skip': skip, 'limit': limit}
            
    def search_receipts(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        with self._get_session() as session:
            from models.customer import Customer
            stmt = select(Receipt).options(
                joinedload(Receipt.customer),
                joinedload(Receipt.invoice)
            ).join(Receipt.customer, isouter=True).where(Receipt.is_deleted == False)
            if query:
                stmt = stmt.where(
                    or_(
                        Receipt.receipt_number.ilike(f"%{query}%"),
                        Receipt.payment_method.ilike(f"%{query}%"),
                        Customer.first_name.ilike(f"%{query}%"),
                        Customer.last_name.ilike(f"%{query}%"),
                        Customer.phone_primary.ilike(f"%{query}%"),
                    )
                )
            
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = session.scalar(count_stmt) or 0
            
            stmt = stmt.order_by(Receipt.created_at.desc()).offset(skip).limit(limit)
            items = list(session.scalars(stmt).all())
            return {'items': items, 'total': total, 'skip': skip, 'limit': limit}
            
    def create_invoice(self, invoice_data: dict, items_data: list, created_by: str) -> Invoice:
        self.validate_required(invoice_data, ['customer_id', 'issue_date', 'due_date', 'total_amount'])
        with self._get_session() as session:
            repo = InvoiceRepository(session)
            count = repo.get_count()
            invoice_data.setdefault('invoice_number', f"INV-{count + 1:05d}")
            
            invoice = Invoice(id=generate_uuid(), created_by=created_by)
            for k, v in invoice_data.items():
                if hasattr(invoice, k):
                    setattr(invoice, k, v)
                    
            for item in items_data:
                new_item = InvoiceItem(id=generate_uuid(), invoice_id=invoice.id, created_by=created_by)
                for k, v in item.items():
                    if hasattr(new_item, k) and k not in ('id', 'invoice_id', 'created_by'):
                        setattr(new_item, k, v)
                session.add(new_item)
                
            repo.add(invoice)
            session.commit()
            session.refresh(invoice)
            return invoice

    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        with self._get_session() as session:
            repo = InvoiceRepository(session)
            return repo.get_by_id(invoice_id)

    def get_invoice_with_details(self, invoice_id: str) -> Optional[Invoice]:
        with self._get_session() as session:
            # Need payment_transactions as well
            stmt = select(Invoice).options(
                joinedload(Invoice.customer), 
                joinedload(Invoice.items),
                joinedload(Invoice.payment_transactions)
            ).where(Invoice.id == invoice_id)
            return session.scalars(stmt).unique().first()
            
    def add_payment_transaction(self, invoice_id: str, amount: float, method: str, ref: str, user_id: str) -> bool:
        with self._get_session() as session:
            invoice = session.get(Invoice, invoice_id)
            if not invoice:
                return False
                
            from models.accounting import PaymentTransaction
            import uuid
            from datetime import date
            
            pt = PaymentTransaction(
                transaction_number=f"PAY-{uuid.uuid4().hex[:6].upper()}",
                invoice_id=invoice_id,
                payment_date=date.today(),
                amount=amount,
                payment_method=method,
                reference_number=ref
            )
            session.add(pt)
            
            invoice.amount_remaining = float(invoice.amount_remaining) - amount
            invoice.amount_paid = float(invoice.amount_paid) + amount
            
            if invoice.amount_remaining <= 0:
                invoice.amount_remaining = 0
                invoice.status = "Paid"
            elif invoice.amount_paid > 0:
                invoice.status = "Partial"
                
            session.commit()
            return True

    def update_invoice(self, invoice_id: str, invoice_data: dict, updated_by: str) -> Optional[Invoice]:
        with self._get_session() as session:
            repo = InvoiceRepository(session)
            invoice = repo.get_by_id(invoice_id)
            if not invoice:
                raise ValueError(f"Invoice {invoice_id} not found.")
            for k, v in invoice_data.items():
                if hasattr(invoice, k) and k not in ('id', 'created_at', 'created_by', 'invoice_number'):
                    setattr(invoice, k, v)
            invoice.updated_by = updated_by
            session.commit()
            session.refresh(invoice)
            return invoice

    def delete_invoice(self, invoice_id: str, deleted_by: str) -> bool:
        with self._get_session() as session:
            repo = InvoiceRepository(session)
            invoice = repo.get_by_id(invoice_id)
            if not invoice:
                raise ValueError(f"Invoice {invoice_id} not found.")
            repo.soft_delete(invoice, deleted_by=deleted_by)
            session.commit()
            return True

    def search_expenses(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        with self._get_session() as session:
            stmt = select(Expense).where(Expense.is_deleted == False)
            if query:
                stmt = stmt.where(
                    or_(
                        Expense.expense_number.ilike(f"%{query}%"),
                        Expense.description.ilike(f"%{query}%")
                    )
                )
            
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = session.scalar(count_stmt) or 0
            
            stmt = stmt.order_by(Expense.created_at.desc()).offset(skip).limit(limit)
            items = list(session.scalars(stmt).all())
            return {'items': items, 'total': total, 'skip': skip, 'limit': limit}

    def create_expense(self, expense_data: dict, created_by: str) -> Expense:
        self.validate_required(expense_data, ['expense_date', 'amount', 'category'])
        with self._get_session() as session:
            repo = ExpenseRepository(session)
            count = repo.get_count()
            expense_data.setdefault('expense_number', f"EXP-{count + 1:05d}")
            
            expense = Expense(id=generate_uuid(), created_by=created_by)
            for k, v in expense_data.items():
                if hasattr(expense, k):
                    setattr(expense, k, v)
            repo.add(expense)
            session.commit()
            session.refresh(expense)
            return expense

    def create_receipt(self, receipt_data: dict, created_by: str) -> Receipt:
        self.validate_required(receipt_data, ['invoice_id', 'customer_id', 'receipt_date', 'amount'])
        with self._get_session() as session:
            repo = ReceiptRepository(session)
            count = repo.get_count()
            receipt_data.setdefault('receipt_number', f"RCT-{count + 1:05d}")
            
            receipt = Receipt(id=generate_uuid(), created_by=created_by)
            for k, v in receipt_data.items():
                if hasattr(receipt, k):
                    setattr(receipt, k, v)
            repo.add(receipt)
            session.commit()
            session.refresh(receipt)
            return receipt

    def get_dashboard_stats(self) -> dict:
        with self._get_session() as session:
            inv_repo = InvoiceRepository(session)
            exp_repo = ExpenseRepository(session)
            total_invoices = inv_repo.get_count()
            unpaid = session.scalar(select(func.count()).select_from(Invoice).where(
                Invoice.status.in_(['Unpaid', 'Partial']), Invoice.is_deleted == False)) or 0
            total_expenses_amount = session.scalar(select(func.sum(Expense.amount)).where(
                Expense.is_deleted == False)) or 0
            return {
                'total_invoices': total_invoices,
                'unpaid_invoices': unpaid,
                'total_expenses': total_expenses_amount,
            }

    def post_standalone_booking(self, customer_id: str, total_amount: float, item_description: str, created_by: str) -> Invoice:
        """Generates an Invoice for a standalone booking (Flight, Visa, Hotel, etc)."""
        invoice_data = {
            'customer_id': customer_id,
            'issue_date': date.today(),
            'due_date': date.today(),
            'total_amount': total_amount,
            'amount_paid': 0.0,
            'amount_remaining': total_amount,
            'status': 'Unpaid'
        }
        items_data = [{
            'description': item_description,
            'quantity': 1,
            'unit_price': total_amount,
            'total_price': total_amount
        }]
        
        invoice = self.create_invoice(invoice_data, items_data, created_by)
        
        from core.signals import app_signals
        app_signals.invoice_generated.emit()
        return invoice

    def get_cashbook_ledger(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        """
        Builds a chronological ledger of Cash IN and Cash OUT transactions.
        Combines Receipts, Expenses, VendorLedger, VendorPayment, and Withdrawals.
        Returns a dict with items, total, and balance.
        """
        with self._get_session() as session:
            from models.accounting import Receipt, Expense, VendorPayment, Withdrawal
            from models.vendor import VendorLedger
            
            transactions = []
            query = query.lower() if query else ""
            
            def match(txt):
                if not query: return True
                return txt and query in str(txt).lower()
            
            # 1. Receipts (Cash IN)
            receipts = session.query(Receipt).where(Receipt.is_deleted == False).all()
            for r in receipts:
                ref = r.receipt_number
                desc = f"Payment from {r.customer.full_name if r.customer else 'Unknown'}"
                if match(ref) or match(desc) or match(r.payment_method):
                    transactions.append({
                        "date": r.receipt_date,
                        "type": "Receipt",
                        "reference": ref,
                        "description": desc,
                        "cash_in": float(r.amount),
                        "cash_out": 0.0,
                        "method": r.payment_method
                    })
                    
            # 2. Expenses (Cash OUT)
            expenses = session.query(Expense).where(Expense.is_deleted == False).all()
            for e in expenses:
                ref = e.expense_number
                desc = e.description or "General Expense"
                if match(ref) or match(desc) or match(e.payment_method):
                    transactions.append({
                        "date": e.expense_date,
                        "type": "Expense",
                        "reference": ref,
                        "description": desc,
                        "cash_in": 0.0,
                        "cash_out": float(e.amount),
                        "method": e.payment_method
                    })
                    
            # 3. Vendor Ledger Payments (Cash OUT)
            # Only debits (payments to vendor)
            v_ledger = session.query(VendorLedger).where(VendorLedger.debit > 0).all()
            for vl in v_ledger:
                ref = f"VL-{str(vl.id)[:6]}"
                desc = f"Payment to Vendor: {vl.vendor.company_name if vl.vendor else 'Unknown'}"
                if vl.description:
                    desc += f" ({vl.description})"
                if match(ref) or match(desc):
                    transactions.append({
                        "date": vl.transaction_date,
                        "type": "Vendor Ledger",
                        "reference": ref,
                        "description": desc,
                        "cash_in": 0.0,
                        "cash_out": float(vl.debit),
                        "method": "N/A"
                    })
                    
            # 4. Legacy Vendor Payments (Cash OUT)
            v_payments = session.query(VendorPayment).all()
            for vp in v_payments:
                ref = vp.payment_number
                desc = f"Payment to {vp.vendor_name}"
                if vp.reference_details:
                    desc += f" ({vp.reference_details})"
                if match(ref) or match(desc) or match(vp.payment_method):
                    transactions.append({
                        "date": vp.date,
                        "type": "Vendor Payment",
                        "reference": ref,
                        "description": desc,
                        "cash_in": 0.0,
                        "cash_out": float(vp.amount),
                        "method": vp.payment_method
                    })
                    
            # 5. Withdrawals (Cash OUT)
            withdrawals = session.query(Withdrawal).all()
            for w in withdrawals:
                ref = w.withdrawal_number
                desc = w.description or "Owner Withdrawal"
                if match(ref) or match(desc):
                    transactions.append({
                        "date": w.date,
                        "type": "Withdrawal",
                        "reference": ref,
                        "description": desc,
                        "cash_in": 0.0,
                        "cash_out": float(w.amount),
                        "method": "Cash/Bank"
                    })
                    
            # Sort by date
            transactions.sort(key=lambda x: x["date"])
            # #region agent log
            try:
                import json, time
                open(r"E:\Customized Travel Agency System\debug-5da8ec.log", "a", encoding="utf-8").write(json.dumps({"sessionId":"5da8ec","hypothesisId":"E","location":"accounting_service.py:get_cashbook_ledger","message":"cashbook built (no InternalTransfer source)","data":{"tx_count":len(transactions),"types":sorted({str(t.get("type")) for t in transactions})},"timestamp":int(time.time()*1000)})+"\n")
            except Exception:
                pass
            # #endregion
            
            # Calculate running balance
            balance = 0.0
            for tx in transactions:
                balance += tx["cash_in"]
                balance -= tx["cash_out"]
                tx["balance"] = balance
                
            # If a query is active, the balance might not reflect the true total balance, 
            # so we sort descending for UI display
            transactions.reverse()
            total = len(transactions)
            items = transactions[skip:skip+limit]
            
            return {'items': items, 'total': total, 'total_balance': balance}

    def get_customer_balances(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        """
        Calculates total_billed, total_paid, and current balance for all customers.
        Supports searching by customer name or phone.
        """
        with self._get_session() as session:
            from models.customer import Customer
            from models.accounting import Invoice, Receipt
            from sqlalchemy import select, func, String, cast
            
            # Subquery for Invoices (Total Billed)
            inv_sub = select(
                Invoice.customer_id,
                func.sum(Invoice.total_amount).label('total_billed')
            ).where(
                (Invoice.is_deleted == False) & (Invoice.status != 'Cancelled')
            ).group_by(Invoice.customer_id).subquery()
            
            # Subquery for Receipts (Total Paid)
            rec_sub = select(
                Receipt.customer_id,
                func.sum(Receipt.amount).label('total_paid')
            ).where(
                Receipt.is_deleted == False
            ).group_by(Receipt.customer_id).subquery()
            
            stmt = select(
                Customer,
                func.coalesce(inv_sub.c.total_billed, 0.0).label('total_billed'),
                func.coalesce(rec_sub.c.total_paid, 0.0).label('total_paid')
            ).outerjoin(
                inv_sub, Customer.id == inv_sub.c.customer_id
            ).outerjoin(
                rec_sub, Customer.id == rec_sub.c.customer_id
            )
            
            if query:
                stmt = stmt.where(
                    or_(
                        Customer.first_name.ilike(f"%{query}%"),
                        Customer.last_name.ilike(f"%{query}%"),
                        Customer.phone_primary.ilike(f"%{query}%")
                    )
                )
                
            results = session.execute(stmt).all()
            
            balances = []
            for row in results:
                customer, total_billed, total_paid = row
                balances.append({
                    'customer': customer,
                    'total_billed': float(total_billed),
                    'total_paid': float(total_paid),
                    'balance': float(total_billed) - float(total_paid)
                })
                
            # Sort by highest balance first
            balances.sort(key=lambda x: x['balance'], reverse=True)
            total = len(balances)
            items = balances[skip:skip+limit]
            return {'items': items, 'total': total}

    def get_customer_ledger(self, customer_id: str) -> list:
        """
        Builds a chronological ledger of Invoice and Receipt transactions for a customer.
        Returns a list of dicts: [date, type, reference, debit, credit, balance]
        """
        with self._get_session() as session:
            from models.accounting import Invoice, Receipt
            
            transactions = []
            
            invoices = session.query(Invoice).where(
                (Invoice.customer_id == customer_id) & 
                (Invoice.is_deleted == False) & 
                (Invoice.status != 'Cancelled')
            ).all()
            
            for inv in invoices:
                transactions.append({
                    "date": inv.issue_date,
                    "type": "Invoice",
                    "reference": inv.invoice_number,
                    "debit": float(inv.total_amount),
                    "credit": 0.0
                })
                
            receipts = session.query(Receipt).where(
                (Receipt.customer_id == customer_id) & 
                (Receipt.is_deleted == False)
            ).all()
            
            for rec in receipts:
                transactions.append({
                    "date": rec.receipt_date,
                    "type": "Receipt",
                    "reference": rec.receipt_number,
                    "debit": 0.0,
                    "credit": float(rec.amount)
                })
                
            transactions.sort(key=lambda x: x["date"])
            
            balance = 0.0
            for tx in transactions:
                balance += tx["debit"]
                balance -= tx["credit"]
                tx["balance"] = balance
                
            return transactions


    def search_quotations(self, query: str = "", skip: int = 0, limit: int = 50) -> dict:
        from models.quotation import Quotation
        from sqlalchemy import or_
        with self._get_session() as session:
            q = session.query(Quotation)
            if query:
                q = q.filter(or_(Quotation.guest_name.ilike(f'%{query}%'), Quotation.id.ilike(f'%{query}%')))
            total = q.count()
            items = q.order_by(Quotation.created_at.desc()).offset(skip).limit(limit).all()
            return {'total': total, 'items': items}
