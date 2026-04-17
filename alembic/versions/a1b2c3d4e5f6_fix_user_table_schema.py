"""Fix user table schema: float columns, rename country_probality, add unique name

Revision ID: a1b2c3d4e5f6
Revises: 66960cfdbcb7
Create Date: 2026-04-17 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '66960cfdbcb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename typo column
    op.alter_column('users', 'country_probality', new_column_name='country_probability')

    # Change gender_probability and country_probability to Float
    op.alter_column('users', 'gender_probability',
                    existing_type=sa.String(),
                    type_=sa.Float(),
                    existing_nullable=False,
                    postgresql_using='gender_probability::double precision')

    op.alter_column('users', 'country_probability',
                    existing_type=sa.String(),
                    type_=sa.Float(),
                    existing_nullable=False,
                    postgresql_using='country_probability::double precision')

    # Add unique constraint on name
    op.create_index('ix_users_name_unique', 'users', ['name'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_users_name_unique', table_name='users')

    op.alter_column('users', 'gender_probability',
                    existing_type=sa.Float(),
                    type_=sa.String(),
                    existing_nullable=False)

    op.alter_column('users', 'country_probability',
                    existing_type=sa.Float(),
                    type_=sa.String(),
                    existing_nullable=False)

    op.alter_column('users', 'country_probability', new_column_name='country_probality')
