from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6928c834149f'
down_revision = '94f7abffbf11'
branch_labels = None
depends_on = None


def upgrade():

    op.add_column(
        'services',
        sa.Column(
            'price',
            sa.Numeric(10, 2),
            nullable=False,
            server_default='0'
        )
    )

    # Remove the temporary database default.
    # The SQLAlchemy model already provides default=0.
    op.alter_column(
        'services',
        'price',
        server_default=None
    )


def downgrade():

    op.drop_column(
        'services',
        'price'
    )