"""
alembic/versions/0001_initial_schema.py
========================================
Initial database schema for TAMS.

Creates all tables for the Travel Agency Management System.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create all TAMS tables.

    Note: This migration is a safety net. Normally Alembic will auto-generate
    migrations from model changes. This first migration ensures the schema is
    created correctly on first run.
    """
    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, default="Employee"),
        sa.Column("status", sa.String(20), nullable=False, default="Active"),
        sa.Column("permissions", sa.JSON, nullable=True),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_login_attempts", sa.Integer, nullable=False, default=0),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("profile_photo", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
    )
    op.create_index("ix_users_username", "users", ["username"])

    # Activity Logs
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("module", sa.String(50), nullable=False),
        sa.Column("record_id", sa.String(36), nullable=True),
        sa.Column("description", sa.Text, nullable=False, default=""),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_activity_logs_user_id", "activity_logs", ["user_id"])

    # Customers
    op.create_table(
        "customers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_code", sa.String(20), nullable=False, unique=True),
        sa.Column("customer_type", sa.String(20), nullable=False, default="Individual"),
        sa.Column("title", sa.String(10), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("father_name", sa.String(200), nullable=True),
        sa.Column("gender", sa.String(10), nullable=True),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("nationality", sa.String(100), nullable=True, default="Pakistani"),
        sa.Column("cnic", sa.String(20), nullable=True),
        sa.Column("passport_number", sa.String(50), nullable=True),
        sa.Column("passport_issue_date", sa.Date, nullable=True),
        sa.Column("passport_expiry_date", sa.Date, nullable=True),
        sa.Column("passport_issue_place", sa.String(200), nullable=True),
        sa.Column("phone_primary", sa.String(20), nullable=False),
        sa.Column("phone_whatsapp", sa.String(20), nullable=True),
        sa.Column("phone_alternate", sa.String(20), nullable=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True, default="Pakistan"),
        sa.Column("marital_status", sa.String(20), nullable=True),
        sa.Column("occupation", sa.String(200), nullable=True),
        sa.Column("profile_photo", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("is_vip", sa.Boolean, nullable=False, default=False),
        sa.Column("credit_limit", sa.Numeric(12, 2), nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
    )
    op.create_index("ix_customers_customer_code", "customers", ["customer_code"])
    op.create_index("ix_customers_cnic", "customers", ["cnic"])
    op.create_index("ix_customers_passport_number", "customers", ["passport_number"])


def downgrade() -> None:
    """Drop all TAMS tables in reverse order."""
    op.drop_table("customers")
    op.drop_table("activity_logs")
    op.drop_table("users")
