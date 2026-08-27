from alembic import op
import sqlalchemy as sa

revision = "0004_user_has_won"
down_revision = "0003_box_selector_name"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("has_won", sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade() -> None:
    op.drop_column("users", "has_won")