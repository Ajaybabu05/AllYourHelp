from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '94f7abffbf11'
down_revision = '652fad3804d6'
branch_labels = None
depends_on = None


def upgrade():

    # Delete old service requests created before
    # the final booking flow was implemented.
    op.execute(
        "DELETE FROM service_requests"
    )

    with op.batch_alter_table(
        'service_requests',
        schema=None
    ) as batch_op:

        batch_op.alter_column(
            'availability_slot_id',
            existing_type=sa.Integer(),
            nullable=False
        )


def downgrade():

    with op.batch_alter_table(
        'service_requests',
        schema=None
    ) as batch_op:

        batch_op.alter_column(
            'availability_slot_id',
            existing_type=sa.Integer(),
            nullable=True
        )