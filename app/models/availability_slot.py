from datetime import datetime

from ..extensions import db


class AvailabilitySlot(db.Model):

    __tablename__ = "availability_slots"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    professional_id = db.Column(
        db.Integer,
        db.ForeignKey("professional_profiles.id"),
        nullable=False
    )

    slot_date = db.Column(
        db.Date,
        nullable=False
    )

    start_time = db.Column(
        db.Time,
        nullable=False
    )

    end_time = db.Column(
        db.Time,
        nullable=False
    )

    is_booked = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    professional = db.relationship(
        "ProfessionalProfile",
        backref=db.backref(
            "availability_slots",
            lazy=True
        )
    )

    def __repr__(self):
        return f"<AvailabilitySlot {self.id}>"