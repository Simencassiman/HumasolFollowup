"""Removed not nullable constraintes from projects components below hierarchy split

Revision ID: baa72137feeb
Revises: d32b720accdb
Create Date: 2023-05-12 18:38:02.522657

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "baa72137feeb"
down_revision = "d32b720accdb"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "energy_project_component",
        "price",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )
    op.alter_column(
        "energy_project_component",
        "efficiency",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )
    op.alter_column(
        "energy_project_component",
        "fuel_cost",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )
    op.alter_column(
        "energy_project_component",
        "overheats",
        existing_type=sa.BOOLEAN(),
        nullable=True,
    )
    op.alter_column(
        "energy_project_component",
        "capacity",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )
    op.alter_column(
        "energy_project_component",
        "battery_type",
        existing_type=postgresql.ENUM(
            "LITHIUM_ION", "LEAD_ACID", name="batterytype"
        ),
        nullable=True,
    )
    op.alter_column(
        "energy_project_component",
        "base_soc",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )
    op.alter_column(
        "energy_project_component",
        "min_soc",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )
    op.alter_column(
        "energy_project_component",
        "max_soc",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )
    op.alter_column(
        "energy_project_component",
        "is_critical",
        existing_type=sa.BOOLEAN(),
        nullable=True,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "energy_project_component",
        "is_critical",
        existing_type=sa.BOOLEAN(),
        nullable=False,
    )
    op.alter_column(
        "energy_project_component",
        "max_soc",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )
    op.alter_column(
        "energy_project_component",
        "min_soc",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )
    op.alter_column(
        "energy_project_component",
        "base_soc",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )
    op.alter_column(
        "energy_project_component",
        "battery_type",
        existing_type=postgresql.ENUM(
            "LITHIUM_ION", "LEAD_ACID", name="batterytype"
        ),
        nullable=False,
    )
    op.alter_column(
        "energy_project_component",
        "capacity",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )
    op.alter_column(
        "energy_project_component",
        "overheats",
        existing_type=sa.BOOLEAN(),
        nullable=False,
    )
    op.alter_column(
        "energy_project_component",
        "fuel_cost",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )
    op.alter_column(
        "energy_project_component",
        "efficiency",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )
    op.alter_column(
        "energy_project_component",
        "price",
        existing_type=postgresql.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )
    # ### end Alembic commands ###