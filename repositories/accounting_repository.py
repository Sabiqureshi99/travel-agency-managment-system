from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from core.base_repository import BaseRepository
from models.accounting import ChartOfAccount, JournalEntry, Invoice, Receipt, Expense

class InvoiceRepository(BaseRepository[Invoice]):
    """Repository for Invoice operations."""
    def __init__(self, session: Session):
        super().__init__(Invoice, session)

    def get_by_id(self, id: str) -> Invoice | None:
        """Get invoice with customer and items eagerly loaded."""
        stmt = select(self.model_class).options(
            joinedload(Invoice.customer),
            joinedload(Invoice.items)
        ).where(self.model_class.id == id, self.model_class.is_deleted == False)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_all(self, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> list[Invoice]:
        """Get all invoices with customers eager loaded."""
        stmt = select(self.model_class).options(
            joinedload(Invoice.customer)
        )
        if not include_deleted:
            stmt = stmt.where(self.model_class.is_deleted == False)
        stmt = stmt.order_by(self.model_class.created_at.desc()).offset(skip).limit(limit)
        return list(self.session.scalars(stmt).all())

class ReceiptRepository(BaseRepository[Receipt]):
    """Repository for Receipt operations."""
    def __init__(self, session: Session):
        super().__init__(Receipt, session)

    def get_all(self, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> list[Receipt]:
        stmt = select(self.model_class).options(
            joinedload(Receipt.customer),
            joinedload(Receipt.invoice)
        )
        if not include_deleted:
            stmt = stmt.where(self.model_class.is_deleted == False)
        stmt = stmt.order_by(self.model_class.created_at.desc()).offset(skip).limit(limit)
        return list(self.session.scalars(stmt).all())

class ExpenseRepository(BaseRepository[Expense]):
    """Repository for Expense operations."""
    def __init__(self, session: Session):
        super().__init__(Expense, session)

class JournalEntryRepository(BaseRepository[JournalEntry]):
    """Repository for JournalEntry operations."""
    def __init__(self, session: Session):
        super().__init__(JournalEntry, session)

class ChartOfAccountRepository(BaseRepository[ChartOfAccount]):
    """Repository for ChartOfAccount operations."""
    def __init__(self, session: Session):
        super().__init__(ChartOfAccount, session)
