from sqlalchemy import select, func, desc
from sqlalchemy.orm import joinedload
from core.base_service import BaseService
from models.customer import Customer
from models.visa import VisaApplication
from models.flight import FlightBooking
from models.accounting import Invoice
from models.user import ActivityLog
from datetime import date

class DashboardService(BaseService):
    def get_kpis(self) -> dict:
        """Fetch high-level KPIs for the dashboard using Financial Engine."""
        from services.financial_engine import FinancialEngineService
        
        with self._get_session() as session:
            total_customers = session.scalar(
                select(func.count()).select_from(Customer).where(Customer.is_deleted == False)
            ) or 0
            
            active_visas = session.scalar(
                select(func.count()).select_from(VisaApplication).where(
                    VisaApplication.is_deleted == False,
                    VisaApplication.status.in_(['Processing', 'Submitted', 'Pending'])
                )
            ) or 0
            
            upcoming_flights = session.scalar(select(func.count()).select_from(FlightBooking).where(
                FlightBooking.booking_status == 'Confirmed',
                FlightBooking.departure_date >= date.today(),
                FlightBooking.is_deleted == False
            )) or 0
            
            today = date.today()
            
            # Today-scoped financials for the "Today's Revenue" KPI card
            today_financials = FinancialEngineService.get_financial_summary(session, today, today)
            
            # All-time financials for cash drawer / bank balance (need full history)
            financials = FinancialEngineService.get_financial_summary(session)
            vendor_payables = FinancialEngineService.get_vendor_payables_summary(session, None, None)

            collections_cash = financials.get("collections_cash", 0.0)
            collections_bank = financials.get("collections_bank", 0.0)
            expenses_cash = financials.get("expenses_cash", 0.0)
            expenses_bank = financials.get("expenses_bank", 0.0)
            
            payments_cash = vendor_payables.get("vendor_payments_cash", 0.0)
            payments_bank = vendor_payables.get("vendor_payments_bank", 0.0)

            cash_in_hand = collections_cash - (expenses_cash + payments_cash)
            bank_balance = collections_bank - (expenses_bank + payments_bank)

            return {
                "total_customers": total_customers,
                "active_visas": active_visas,
                "upcoming_flights": upcoming_flights,
                "gross_sales": today_financials.get("gross_sales", 0.0),  # TODAY only
                "collections": today_financials.get("collections", 0.0),
                "customer_dues": financials.get("customer_dues", 0.0),    # all-time dues
                "net_profit": today_financials.get("net_profit", 0.0),    # TODAY only
                "cash_in_hand": cash_in_hand,
                "bank_balance": bank_balance
            }

    def get_recent_activity(self, limit: int = 15) -> list:
        """Fetch recent activity logs."""
        with self._get_session() as session:
            stmt = select(ActivityLog).options(
                joinedload(ActivityLog.user)
            ).order_by(desc(ActivityLog.created_at)).limit(limit)
            
            logs = session.scalars(stmt).all()
            
            result = []
            for log in logs:
                username = log.user.username if log.user else "System"
                result.append({
                    "id": log.id,
                    "action": log.action,
                    "module": log.module,
                    "description": log.description,
                    "created_at": log.created_at,
                    "username": username
                })
            return result
