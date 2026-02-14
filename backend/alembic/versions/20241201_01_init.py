"""init

Revision ID: 20241201_01
Revises:
Create Date: 2024-12-01
"""

from alembic import op
import sqlalchemy as sa

revision = "20241201_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.BigInteger(), primary_key=True), sa.Column("username", sa.String(64), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table("conversations", sa.Column("id", sa.BigInteger(), primary_key=True), sa.Column("is_group", sa.Boolean(), server_default=sa.text("false"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))

    op.create_table("messages", sa.Column("id", sa.BigInteger(), primary_key=True), sa.Column("conversation_id", sa.BigInteger(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False), sa.Column("sender_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("text", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table("refresh_tokens", sa.Column("id", sa.BigInteger(), primary_key=True), sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("token_hash", sa.String(128), nullable=False), sa.Column("revoked", sa.Boolean(), server_default=sa.text("false"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False))

    op.create_table("participants", sa.Column("id", sa.BigInteger(), primary_key=True), sa.Column("conversation_id", sa.BigInteger(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False), sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("last_read_message_id", sa.BigInteger(), sa.ForeignKey("messages.id"), nullable=True), sa.UniqueConstraint("conversation_id", "user_id", name="uq_participant"))

    op.create_table("message_deletes", sa.Column("id", sa.BigInteger(), primary_key=True), sa.Column("message_id", sa.BigInteger(), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False), sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("deleted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.UniqueConstraint("message_id", "user_id", name="uq_message_delete"))

    op.create_table("attachments", sa.Column("id", sa.BigInteger(), primary_key=True), sa.Column("message_id", sa.BigInteger(), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False), sa.Column("kind", sa.String(30), nullable=False), sa.Column("url", sa.String(255), nullable=False), sa.Column("mime", sa.String(100), nullable=False), sa.Column("size", sa.Integer(), nullable=False), sa.Column("width", sa.Integer(), nullable=True), sa.Column("height", sa.Integer(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))


def downgrade() -> None:
    op.drop_table("attachments")
    op.drop_table("message_deletes")
    op.drop_table("participants")
    op.drop_table("refresh_tokens")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
