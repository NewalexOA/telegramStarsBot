"""Add unique constraint to ReferralLink.user_id

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2024-11-01 14:00:00.000000
"""
from alembic import op

def upgrade():
    # Удаляем дубликаты, оставляя только последнюю ссылку для каждого пользователя
    op.execute("""
        DELETE FROM referral_links
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM referral_links
            GROUP BY user_id
        )
    """)
    
    # Добавляем ограничение unique
    op.create_unique_constraint(
        'uq_referral_links_user_id',
        'referral_links',
        ['user_id']
    )

def downgrade():
    op.drop_constraint(
        'uq_referral_links_user_id',
        'referral_links'
    ) 