"""Added user fs_uniquifier

Revision ID: d2a8ad152673
Revises: e9923e4262fc
Create Date: 2022-11-24 18:35:20.550301

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d2a8ad152673"
down_revision = "e9923e4262fc"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user",
        sa.Column("fs_uniquifier", sa.String(length=255), nullable=False),
    )
    op.create_unique_constraint(None, "user", ["fs_uniquifier"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "user", type_="unique")
    op.drop_column("user", "fs_uniquifier")
    # ### end Alembic commands ###
