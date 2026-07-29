# Plan Reference: §888/CR-STO-01
from alembic import op
import sqlalchemy as sa

revision = '001_extensions_timescale'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS timescaledb')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE SCHEMA IF NOT EXISTS shipsense')
    op.execute('SET search_path TO shipsense, public')

def downgrade() -> None:
    op.execute('DROP SCHEMA IF EXISTS shipsense CASCADE')
