from alembic import op
import sqlalchemy as sa

revision = "0003_box_selector_name"
down_revision = "0002_box_availability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("boxes", sa.Column("selected_by_name", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("boxes", "selected_by_name")