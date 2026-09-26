from sqlalchemy import func, select
from datetime import date, timedelta
from typing import List, Dict
from models.accounting import Invoice, Receipt, JournalEntry, JournalLine, ChartOfAccount, Expense, InternalTransfer
from models.customer import Customer
from models.flight import FlightBooking
from models.umrah import CustomUmrahBooking
from models.visa import VisaApplication
from models.hotel import HotelBooking
from models.booking import Booking
from models.vendor import VendorLedger

class FinancialEngineService:
    @staticmethod
    def get_financial_summary(session, start_date: date | None = None, end_date: date | None = None) -> dict:
        """Aggregates high-level KPIs safely handling null dates."""
        
        # Base query filters
        inv_filter = [Invoice.issue_date >= start_date, Invoice.issue_date <= end_date] if start_date and end_date else []
        rcpt_filter = [Receipt.receipt_date >= start_date, Receipt.receipt_date <= end_date] if start_date and end_date else []
        jrn_filter = [JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date] if start_date and end_date else []

        # 1. Gross Sales (Invoiced Revenue)
        gross_sales = session.query(func.coalesce(func.sum(Invoice.total_amount), 0.0))\
            .filter(*inv_filter).scalar()
            
        # 2. Total Collections (Cash Flow/Inflow)
        collections = session.query(func.coalesce(func.sum(Receipt.amount), 0.0))\
            .filter(*rcpt_filter).scalar()
            
        collections_cash = session.query(func.coalesce(func.sum(Receipt.amount), 0.0))\
            .filter(*rcpt_filter, Receipt.payment_method == 'Cash').scalar()
            
        collections_bank = float(collections) - float(collections_cash)
        
        # Account for InternalTransfers: Cash → Bank moves reduce cash and increase bank
        trf_filter = [InternalTransfer.transfer_date >= start_date, InternalTransfer.transfer_date <= end_date] if start_date and end_date else []
        total_transferred = session.query(func.coalesce(func.sum(InternalTransfer.amount), 0.0))\
            .filter(*trf_filter).scalar()
        total_transferred = float(total_transferred)
        
        # Cash loses transferred amount; Bank gains it
        collections_cash_adjusted = float(collections_cash) - total_transferred
        collections_bank_adjusted = collections_bank + total_transferred
            
        # 3. Customer Dues (Receivables)
        customer_dues = gross_sales - collections

        # 4. Cost of Goods Sold (COGS) – sum purchase costs from unified Booking model with date filter
        booking_filter = [Booking.is_deleted == False]
        if start_date and end_date:
            booking_filter.extend([func.date(Booking.created_at) >= start_date, func.date(Booking.created_at) <= end_date])
            
        cogs = session.query(func.coalesce(func.sum(Booking.total_cost_sql_expr()), 0.0))\
            .filter(*booking_filter).scalar()
            
        cogs = float(cogs)
        
        gross_profit = float(gross_sales) - cogs

        # 5. Operating Expenses (General Ledger EXPENSE entries + Direct Expenses table)
        journal_expenses = session.query(func.coalesce(func.sum(JournalLine.debit_amount - JournalLine.credit_amount), 0.0))\
            .join(JournalEntry, JournalLine.journal_entry_id == JournalEntry.id)\
            .join(ChartOfAccount, JournalLine.account_id == ChartOfAccount.id)\
            .filter(ChartOfAccount.account_type == 'Expense', *jrn_filter).scalar()
            
        exp_filter = [Expense.expense_date >= start_date, Expense.expense_date <= end_date] if start_date and end_date else []
        direct_expenses = session.query(func.coalesce(func.sum(Expense.amount), 0.0))\
            .filter(*exp_filter, Expense.is_deleted == False).scalar()
            
        expenses_cash = session.query(func.coalesce(func.sum(Expense.amount), 0.0))\
            .filter(*exp_filter, Expense.is_deleted == False, Expense.payment_source == 'Cash Drawer').scalar()
            
        expenses_bank = float(direct_expenses) - float(expenses_cash)
            
        total_expenses = float(journal_expenses) + float(direct_expenses)
            
        net_profit = gross_profit - total_expenses
        
        # Calculate Profits stuck in dues
        # Simplified calculation: (Customer Dues / Gross Sales) * Gross Profit
        stuck_profit = 0.0
        if gross_sales > 0:
            stuck_profit = float(gross_profit) * (float(customer_dues) / float(gross_sales))

        return {
            "gross_sales": float(gross_sales),
            "cogs": float(cogs),
            "gross_profit": float(gross_profit),
            "total_expenses": float(total_expenses),
            "net_profit": float(net_profit),
            "collections": float(collections),
            "collections_cash": collections_cash_adjusted,
            "collections_bank": collections_bank_adjusted,
            "expenses_cash": float(expenses_cash),
            "expenses_bank": float(expenses_bank),
            "customer_dues": float(customer_dues),
            "stuck_profit": float(stuck_profit)
        }

    @staticmethod
    def get_vendor_payables_summary(session, start_date: date | None = None, end_date: date | None = None) -> dict:
        """Returns total bills (credits), total payments (debits), and outstanding debt for vendors."""
        vl_filter = []
        if start_date and end_date:
            vl_filter = [VendorLedger.transaction_date >= start_date, VendorLedger.transaction_date <= end_date]

        total_bills = session.query(func.coalesce(func.sum(VendorLedger.credit), 0.0)).filter(*vl_filter).scalar()
        total_payments = session.query(func.coalesce(func.sum(VendorLedger.debit), 0.0)).filter(*vl_filter).scalar()
        
        payments_cash = session.query(func.coalesce(func.sum(VendorLedger.debit), 0.0))\
            .filter(*vl_filter, VendorLedger.payment_source == 'Cash Drawer').scalar()
            
        payments_bank = total_payments - payments_cash
        
        # Total debt is the overall running balance (Credit - Debit), we might want it without date filter to see true debt
        total_debt = session.query(func.coalesce(func.sum(VendorLedger.credit - VendorLedger.debit), 0.0)).scalar()

        return {
            "total_vendor_bills": float(total_bills),
            "total_vendor_payments": float(total_payments),
            "vendor_payments_cash": float(payments_cash),
            "vendor_payments_bank": float(payments_bank),
            "total_outstanding_debt": float(total_debt)
        }

    @staticmethod
    def get_booking_volume_and_profit(session, start_date: date | None = None, end_date: date | None = None) -> List[Dict]:
        """Returns booking volume and profit broken down by booking type."""
        b_filter = [Booking.is_deleted == False]
        if start_date and end_date:
            # Using created_at for filtering volume
            b_filter.extend([Booking.created_at >= start_date, Booking.created_at <= end_date])
            
        stmt = session.query(
            Booking.booking_type,
            func.count(Booking.id).label('volume'),
            func.sum(Booking.total_revenue_sql_expr()).label('revenue'),
            func.sum(Booking.total_revenue_sql_expr() - Booking.total_cost_sql_expr()).label('profit')
        ).filter(*b_filter).group_by(Booking.booking_type)

        results = []
        for row in stmt.all():
            results.append({
                "booking_type": row.booking_type,
                "volume": int(row.volume),
                "revenue": float(row.revenue or 0),
                "profit": float(row.profit or 0)
            })
        return results

    @staticmethod
    def get_profit_and_loss_statement(session, start_date: date, end_date: date) -> dict:
        """Detailed breakdown for the P&L Report Tab."""
        summary = FinancialEngineService.get_financial_summary(session, start_date, end_date)
        
        # Itemized Expenses breakdown by Account Name
        expenses_query = session.query(
            ChartOfAccount.account_name,
            func.coalesce(func.sum(JournalLine.debit_amount - JournalLine.credit_amount), 0.0).label('amount')
        ).join(JournalLine).join(JournalEntry)\
         .filter(ChartOfAccount.account_type == 'Expense', JournalEntry.entry_date.between(start_date, end_date))\
         .group_by(ChartOfAccount.account_name).all()
         
        direct_expenses_query = session.query(
            ChartOfAccount.account_name,
            func.coalesce(func.sum(Expense.amount), 0.0).label('amount')
        ).join(ChartOfAccount, Expense.account_id == ChartOfAccount.id)\
         .filter(Expense.expense_date.between(start_date, end_date), Expense.is_deleted == False)\
         .group_by(ChartOfAccount.account_name).all()
         
        expense_dict = {}
        for row in expenses_query:
            expense_dict[row[0]] = float(row[1])
            
        for row in direct_expenses_query:
            expense_dict[row[0]] = expense_dict.get(row[0], 0.0) + float(row[1])
            
        itemized_expenses = [{"account": k, "amount": v} for k, v in expense_dict.items()]
        summary["itemized_expenses"] = itemized_expenses
        return summary

    @staticmethod
    def get_receivables_aging_report(session) -> List[Dict]:
        """Calculates aging brackets for customer receivables."""
        today = date.today()
        aging_data = []
        
        # Get all customers who have at least one invoice with amount_remaining > 0
        open_invoices_query = session.query(Invoice).filter(Invoice.amount_remaining > 0).all()
        
        # Group open invoices by customer
        customer_invoices = {}
        for inv in open_invoices_query:
            if inv.customer_id not in customer_invoices:
                customer_invoices[inv.customer_id] = []
            customer_invoices[inv.customer_id].append(inv)
            
        for customer_id, invoices in customer_invoices.items():
            customer = session.query(Customer).filter_by(id=customer_id).first()
            if not customer:
                continue
                
            aging_0_30 = aging_31_60 = aging_60_plus = 0.0
            total_outstanding = 0.0
            
            for inv in invoices:
                amount_remaining = float(inv.amount_remaining)
                total_outstanding += amount_remaining
                
                days_overdue = (today - (inv.due_date or inv.issue_date)).days
                if days_overdue > 60:
                    aging_60_plus += amount_remaining
                elif days_overdue > 30:
                    aging_31_60 += amount_remaining
                else:
                    aging_0_30 += amount_remaining
                    
            aging_data.append({
                "customer_name": customer.full_name,
                "total_open_invoices": len(invoices),
                "total_outstanding": total_outstanding,
                "0_30_days": aging_0_30,
                "31_60_days": aging_31_60,
                "60_plus_days": aging_60_plus
            })
            
        return sorted(aging_data, key=lambda x: x['total_outstanding'], reverse=True)
