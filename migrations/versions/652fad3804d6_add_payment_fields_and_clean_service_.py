from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '652fad3804d6'
down_revision = '621fbf26043e'
branch_labels = None
depends_on = None


def upgrade():

    with op.batch_alter_table(
        'service_requests',
        schema=None
    ) as batch_op:

        # Payment information
        batch_op.add_column(
            sa.Column(
                'payment_status',
                sa.String(length=30),
                nullable=True
            )
        )

        batch_op.add_column(
            sa.Column(
                'payment_id',
                sa.String(length=255),
                nullable=True
            )
        )

        batch_op.add_column(
            sa.Column(
                'payment_amount',
                sa.Numeric(10, 2),
                nullable=True
            )
        )


def downgrade():

    with op.batch_alter_table(
        'service_requests',
        schema=None
    ) as batch_op:

        batch_op.drop_column('payment_amount')
        batch_op.drop_column('payment_id')
        batch_op.drop_column('payment_status')