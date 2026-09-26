import logging
from typing import Dict, Any
from datetime import datetime, date
from core.base_service import BaseService
from sqlalchemy import select, func
from models.accounting import Invoice, Receipt, Expense, JournalEntry, JournalLine, ChartOfAccount
from models.booking import Booking
from services.financial_engine import FinancialEngineService

logger = logging.getLogger(__name__)

class ReportServiceError(Exception):
    pass

class ReportService(BaseService):
    def get_financial_statement_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        try:
            with self._get_session() as session:
                # 1. Fetch P&L and Summary from Financial Engine
                pl_data = FinancialEngineService.get_profit_and_loss_statement(session, start_date, end_date)
                
                # 2. Fetch Receipts for Cash Collections Tab
                receipts_stmt = select(Receipt).where(
                    Receipt.is_deleted == False,
                    Receipt.receipt_date >= start_date,
                    Receipt.receipt_date <= end_date
                ).order_by(Receipt.receipt_date.desc())
                
                receipts = list(session.scalars(receipts_stmt).all())
                
                receipts_list = []
                for r in receipts:
                    # Normalize payment_method → 'Cash' or 'Bank'
                    # Only 'Cash' stays in Cash Flow; Bank Transfer, Cheque, Card, etc. → Bank Flow
                    raw_pm = (r.payment_method or "Cash").strip()
                    norm_pm = "Cash" if raw_pm.lower() == "cash" else "Bank"
                    receipts_list.append({
                        "date": r.receipt_date.isoformat(),
                        "receipt_number": r.receipt_number,
                        "customer": r.customer.full_name if r.customer else 'Cash Customer',
                        "payment_method": norm_pm,
                        "amount": float(r.amount),
                        "type": "IN"
                    })
                    
                # 3. Fetch Expenses to include in the same log
                expenses_stmt = select(Expense).where(
                    Expense.is_deleted == False,
                    Expense.expense_date >= start_date,
                    Expense.expense_date <= end_date
                ).order_by(Expense.expense_date.desc())
                
                expenses = list(session.scalars(expenses_stmt).all())
                
                for e in expenses:
                    # Use payment_source (Cash/Bank enum) to correctly route the entry
                    src = e.payment_source.value if e.payment_source else "Cash"  # "Cash" or "Bank"
                    
                    # Build a rich party label: Category | Description | Bank
                    parts = []
                    if e.account and e.account.account_name:
                        parts.append(e.account.account_name)
                    if e.description:
                        parts.append(e.description)
                    elif e.reference:
                        parts.append(e.reference)
                    if src == "Bank" and e.bank_account_name:
                        parts.append(f"[{e.bank_account_name}]")
                    
                    party_label = " | ".join(parts) if parts else "Expense"
                    
                    receipts_list.append({
                        "date": e.expense_date.isoformat(),
                        "receipt_number": e.expense_number,
                        "customer": party_label,
                        "payment_method": src,   # "Cash" or "Bank" — matches PDF filter
                        "amount": float(e.amount),
                        "type": "OUT"
                    })
                # 4. Fetch Vendor Payments (Cash OUT)
                from models.vendor import VendorLedger
                vendor_ledger_stmt = select(VendorLedger).where(
                    VendorLedger.debit > 0,
                    VendorLedger.transaction_date >= start_date,
                    VendorLedger.transaction_date <= end_date
                ).order_by(VendorLedger.transaction_date.desc())
                
                vendor_payments = list(session.scalars(vendor_ledger_stmt).all())
                
                total_vendor_payments = 0.0
                for vp in vendor_payments:
                    amt = float(vp.debit)
                    total_vendor_payments += amt
                    # Normalize payment_source → 'Cash' or 'Bank' so PDF filters match
                    raw_source = (vp.payment_source or "Bank").lower()
                    if "cash" in raw_source:
                        norm_method = "Cash"
                    else:
                        norm_method = "Bank"
                    receipts_list.append({
                        "date": vp.transaction_date.isoformat() if vp.transaction_date else "",
                        "receipt_number": f"VP-{str(vp.id)[:6]}",
                        "customer": vp.vendor.company_name if vp.vendor else 'Unknown Vendor',
                        "payment_method": norm_method,
                        "amount": amt,
                        "type": "OUT"
                    })
                
                # 5. Fetch Internal Transfers (Cash → Bank) and add to log
                from models.accounting import InternalTransfer
                transfer_stmt = select(InternalTransfer).where(
                    InternalTransfer.transfer_date >= start_date,
                    InternalTransfer.transfer_date <= end_date
                ).order_by(InternalTransfer.transfer_date.desc())
                
                transfers = list(session.scalars(transfer_stmt).all())
                # #region agent log
                try:
                    import json, time
                    open(r"E:\Customized Travel Agency System\debug-5da8ec.log", "a", encoding="utf-8").write(json.dumps({"sessionId":"5da8ec","hypothesisId":"B","location":"report_service.py:get_financial_statement_report","message":"transfers queried for flow log","data":{"start_date":str(start_date),"end_date":str(end_date),"transfer_count":len(transfers),"transfer_dates":[str(t.transfer_date) for t in transfers],"transfer_ids":[str(t.id)[:8] for t in transfers]},"timestamp":int(time.time()*1000)})+"\n")
                except Exception:
                    pass
                # #endregion
                for t in transfers:
                    amt = float(t.amount)
                    bank_label = t.destination_bank_account or "Bank"
                    # Cash drawer loses this amount (Cash OUT)
                    receipts_list.append({
                        "date": t.transfer_date.isoformat(),
                        "receipt_number": f"TRF-{str(t.id)[:6].upper()}",
                        "customer": f"→ Transferred to {bank_label}",
                        "payment_method": "Cash",
                        "amount": amt,
                        "type": "OUT"
                    })
                    # Bank account gains this amount (Bank IN)
                    receipts_list.append({
                        "date": t.transfer_date.isoformat(),
                        "receipt_number": f"TRF-{str(t.id)[:6].upper()}",
                        "customer": f"← Cash Deposit from Drawer",
                        "payment_method": "Bank",
                        "amount": amt,
                        "type": "IN"
                    })
                
                # Sort the combined list by date descending
                receipts_list.sort(key=lambda x: x["date"], reverse=True)
                # #region agent log
                try:
                    import json as _json
                    _trf = [r for r in receipts_list if str(r.get("receipt_number","")).startswith("TRF-")]
                    with open(r"E:\Customized Travel Agency System\debug-5da8ec.log", "a", encoding="utf-8") as _f:
                        _f.write(_json.dumps({"sessionId":"5da8ec","hypothesisId":"C","location":"report_service.py:receipts_log","message":"receipts_log_built","data":{"total":len(receipts_list),"trf_count":len(_trf),"trf_methods":[r.get("payment_method") for r in _trf],"trf_types":[r.get("type") for r in _trf]},"timestamp":int(__import__("time").time()*1000)})+"\n")
                except Exception:
                    pass
                # #endregion

                # 5. Fetch Advanced Metrics
                vendor_payables = FinancialEngineService.get_vendor_payables_summary(session, start_date, end_date)
                booking_profits = FinancialEngineService.get_booking_volume_and_profit(session, start_date, end_date)
                receivables_aging = FinancialEngineService.get_receivables_aging_report(session)

                # Ensure strict keys as requested
                return {
                    "gross_revenue": pl_data.get("gross_sales", 0.0),
                    "cogs": pl_data.get("cogs", 0.0),
                    "gross_profit": pl_data.get("gross_profit", 0.0),
                    "itemized_expenses": pl_data.get("itemized_expenses", []),
                    "total_expenses": pl_data.get("total_expenses", 0.0),
                    "net_profit": pl_data.get("net_profit", 0.0),
                    "total_collections": pl_data.get("collections", 0.0),
                    "collections_cash": pl_data.get("collections_cash", 0.0),
                    "collections_bank": pl_data.get("collections_bank", 0.0),
                    "expenses_cash": pl_data.get("expenses_cash", 0.0),
                    "expenses_bank": pl_data.get("expenses_bank", 0.0),
                    "total_vendor_payments": vendor_payables.get("total_vendor_payments", total_vendor_payments),
                    "vendor_payments_cash": vendor_payables.get("vendor_payments_cash", 0.0),
                    "vendor_payments_bank": vendor_payables.get("vendor_payments_bank", 0.0),
                    "receipts_log": receipts_list,
                    
                    # New Advanced Metrics
                    "customer_dues": pl_data.get("customer_dues", 0.0),
                    "stuck_profit": pl_data.get("stuck_profit", 0.0),
                    "total_vendor_bills": vendor_payables.get("total_vendor_bills", 0.0),
                    "total_outstanding_debt": vendor_payables.get("total_outstanding_debt", 0.0),
                    "booking_profits": booking_profits,
                    "receivables_aging": receivables_aging
                }
        except Exception as e:
            logger.error(f"Error generating financial statement report: {e}")
            raise ReportServiceError(f"Error generating report: {e}") from e

    def generate_financial_profit_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Calculates profit across all booking types from the central Booking model, 
        and deducts total expenses for true net profit.
        """
        try:
            with self._get_session() as session:
                # 1. Group by Booking Type
                stmt = select(
                    Booking.booking_type,
                    func.sum(Booking.total_revenue_sql_expr()).label('total_revenue'),
                    func.sum(Booking.total_cost_sql_expr()).label('total_cost'),
                    func.sum(Booking.total_revenue_sql_expr() - Booking.total_cost_sql_expr()).label('total_profit')
                ).where(
                    Booking.is_deleted == False,
                    func.date(Booking.created_at) >= start_date,
                    func.date(Booking.created_at) <= end_date
                ).group_by(Booking.booking_type)
                
                results = session.execute(stmt).all()
                
                breakdown = []
                total_revenue = 0.0
                total_cost = 0.0
                total_gross_profit = 0.0
                
                for row in results:
                    b_type = row.booking_type
                    rev = float(row.total_revenue or 0)
                    cst = float(row.total_cost or 0)
                    prof = float(row.total_profit or 0)
                    
                    total_revenue += rev
                    total_cost += cst
                    total_gross_profit += prof
                    
                    breakdown.append({
                        "booking_type": b_type,
                        "revenue": rev,
                        "cost": cst,
                        "gross_profit": prof
                    })
                
                # 2. Subtract Expenses
                expense_stmt = select(func.sum(Expense.amount)).where(
                    Expense.is_deleted == False,
                    Expense.expense_date >= start_date,
                    Expense.expense_date <= end_date
                )
                total_expenses = float(session.scalar(expense_stmt) or 0.0)
                
                net_profit = total_gross_profit - total_expenses
                
                return {
                    "breakdown": breakdown,
                    "total_revenue": total_revenue,
                    "total_cost": total_cost,
                    "total_gross_profit": total_gross_profit,
                    "total_expenses": total_expenses,
                    "true_net_profit": net_profit
                }
        except Exception as e:
            logger.error(f"Error generating financial profit report: {e}")
            raise ReportServiceError(f"Error generating profit report: {e}") from e
