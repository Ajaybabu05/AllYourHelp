from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c977058a0e1'
down_revision = '702a235ca880'
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        'availability_slots',

        sa.Column(
            'id',
            sa.Integer(),
            primary_key=True
        ),

        sa.Column(
            'professional_id',
            sa.Integer(),
            sa.ForeignKey('professional_profiles.id'),
            nullable=False
        ),

        sa.Column(
            'slot_date',
            sa.Date(),
            nullable=False
        ),

        sa.Column(
            'start_time',
            sa.Time(),
            nullable=False
        ),

        sa.Column(
            'end_time',
            sa.Time(),
            nullable=False
        ),

        sa.Column(
            'is_booked',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false()
        ),

        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now()
        )
    )


def downgrade():

    op.drop_table('availability_slots')