from alembic import op
import sqlalchemy as sa

revision = "0002_box_availability"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("boxes", sa.Column("is_available", sa.Boolean(), server_default=sa.true(), nullable=False))


def downgrade() -> None:
    op.drop_column("boxes", "is_available")
