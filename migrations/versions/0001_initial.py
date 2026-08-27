from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("telegram_id", sa.BigInteger(), nullable=False), sa.Column("username", sa.String(255)), sa.Column("first_name", sa.String(255)), sa.Column("last_name", sa.String(255)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("is_blocked", sa.Boolean(), server_default=sa.false(), nullable=False), sa.UniqueConstraint("telegram_id"))
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])
    op.create_table("boxes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("box_number", sa.Integer(), nullable=False), sa.Column("gift_amount", sa.Integer(), server_default="0", nullable=False), sa.Column("is_winner", sa.Boolean(), server_default=sa.false(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("box_number"), sa.CheckConstraint("box_number BETWEEN 1 AND 100"), sa.CheckConstraint("gift_amount >= 0"))
    op.create_index("ix_boxes_box_number", "boxes", ["box_number"])
    op.create_table("game_attempts", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("box_number", sa.Integer(), nullable=False), sa.Column("gift_amount", sa.Integer(), nullable=False), sa.Column("is_winner", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_game_attempts_user_id", "game_attempts", ["user_id"])
    op.create_index("ix_game_attempts_created_at", "game_attempts", ["created_at"])


def downgrade() -> None:
    op.drop_table("game_attempts")
    op.drop_table("boxes")
    op.drop_table("users")
