"""add_categorical_pax_pricing

Revision ID: c1a2b3d4e5f6
Revises: 7a3f31d4267e
Create Date: 2026-09-22 11:00:00.000000+00:00

Summary
-------
Phase 1 — Categorical PAX Pricing (Adult / Child / Infant).

Changes to the ``bookings`` table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* ADD  adult_count            INTEGER  NOT NULL DEFAULT 0
* ADD  adult_cost_price       NUMERIC(12,2) NOT NULL DEFAULT 0.00
* ADD  adult_selling_price    NUMERIC(12,2) NOT NULL DEFAULT 0.00
* ADD  child_count            INTEGER  NOT NULL DEFAULT 0
* ADD  child_cost_price       NUMERIC(12,2) NOT NULL DEFAULT 0.00
* ADD  child_selling_price    NUMERIC(12,2) NOT NULL DEFAULT 0.00
* ADD  infant_count           INTEGER  NOT NULL DEFAULT 0
* ADD  infant_cost_price      NUMERIC(12,2) NOT NULL DEFAULT 0.00
* ADD  infant_selling_price   NUMERIC(12,2) NOT NULL DEFAULT 0.00

* The legacy  ``cost_price``, ``selling_price``, and ``net_profit``
  columns are DROPPED.  Any existing row data that must be preserved
  should be migrated *before* running this migration.  A data-salvage
  guard is provided below (see the ``_migrate_legacy_data`` helper).

Changes to the ``pax`` table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* ADD  pax_type  VARCHAR(10)  NOT NULL DEFAULT 'Adult'

Rollback (downgrade)
~~~~~~~~~~~~~~~~~~~~~
Restores the three legacy columns on ``bookings`` and drops the new
categorical columns.  The ``pax_type`` column is dropped from ``pax``.

Note: SQLite does not support DROP COLUMN before v3.35.  The
``render_as_batch=True`` option in env.py covers this via a table-rebuild
strategy for all ALTER TABLE operations.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, None] = "7a3f31d4267e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Data-salvage helper — run BEFORE column drops
# ---------------------------------------------------------------------------

def _migrate_legacy_data(connection: sa.engine.Connection) -> None:
    """
    Best-effort migration of legacy flat prices into the new Adult tier.

    Logic:
        adult_count        = 1   (at minimum; we cannot infer the actual headcount)
        adult_cost_price   = legacy cost_price   (existing cost per the booking)
        adult_selling_price= legacy selling_price

    This is a conservative placeholder.  Operators should review migrated
    records and adjust counts/prices in the UI post-migration.
    """
    connection.execute(
        sa.text(
            """
            UPDATE bookings
            SET
                adult_count          = 1,
                adult_cost_price     = COALESCE(cost_price, 0.00),
                adult_selling_price  = COALESCE(selling_price, 0.00)
            WHERE adult_count IS NULL OR adult_count = 0
            """
        )
    )


# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1.  bookings — add the nine categorical pricing columns              #
    # ------------------------------------------------------------------ #
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        # Adult tier
        batch_op.add_column(
            sa.Column(
                "adult_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "adult_cost_price",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                server_default="0.00",
            )
        )
        batch_op.add_column(
            sa.Column(
                "adult_selling_price",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                server_default="0.00",
            )
        )

        # Child tier
        batch_op.add_column(
            sa.Column(
                "child_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "child_cost_price",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                server_default="0.00",
            )
        )
        batch_op.add_column(
            sa.Column(
                "child_selling_price",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                server_default="0.00",
            )
        )

        # Infant tier
        batch_op.add_column(
            sa.Column(
                "infant_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "infant_cost_price",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                server_default="0.00",
            )
        )
        batch_op.add_column(
            sa.Column(
                "infant_selling_price",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                server_default="0.00",
            )
        )

    # ------------------------------------------------------------------ #
    # 2.  Salvage legacy data BEFORE dropping the old columns              #
    # ------------------------------------------------------------------ #
    bind = op.get_bind()
    _migrate_legacy_data(bind)

    # ------------------------------------------------------------------ #
    # 3.  bookings — drop the three legacy columns                         #
    # ------------------------------------------------------------------ #
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.drop_column("net_profit")
        batch_op.drop_column("selling_price")
        batch_op.drop_column("cost_price")

    # ------------------------------------------------------------------ #
    # 4.  pax — add pax_type column                                        #
    # ------------------------------------------------------------------ #
    with op.batch_alter_table("pax", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "pax_type",
                sa.String(length=10),
                nullable=False,
                server_default="Adult",
            )
        )


# ---------------------------------------------------------------------------
# downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1.  pax — remove pax_type column                                     #
    # ------------------------------------------------------------------ #
    with op.batch_alter_table("pax", schema=None) as batch_op:
        batch_op.drop_column("pax_type")

    # ------------------------------------------------------------------ #
    # 2.  bookings — restore the three legacy columns                      #
    # ------------------------------------------------------------------ #
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "cost_price",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                server_default="0.00",
            )
        )
        batch_op.add_column(
            sa.Column(
                "selling_price",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                server_default="0.00",
            )
        )
        batch_op.add_column(
            sa.Column(
                "net_profit",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                server_default="0.00",
            )
        )

    # Restore best-effort flat cost/revenue from Adult tier (lossy)
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE bookings
            SET
                cost_price    = adult_count * adult_cost_price,
                selling_price = adult_count * adult_selling_price,
                net_profit    = (adult_count * adult_selling_price)
                                - (adult_count * adult_cost_price)
            """
        )
    )

    # ------------------------------------------------------------------ #
    # 3.  bookings — drop the nine categorical columns                     #
    # ------------------------------------------------------------------ #
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.drop_column("infant_selling_price")
        batch_op.drop_column("infant_cost_price")
        batch_op.drop_column("infant_count")
        batch_op.drop_column("child_selling_price")
        batch_op.drop_column("child_cost_price")
        batch_op.drop_column("child_count")
        batch_op.drop_column("adult_selling_price")
        batch_op.drop_column("adult_cost_price")
        batch_op.drop_column("adult_count")
