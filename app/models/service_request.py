from datetime import datetime

from ..extensions import db


class ServiceRequest(db.Model):

    __tablename__ = "service_requests"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # User who is booking the service
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Professional providing the service
    professional_id = db.Column(
        db.Integer,
        db.ForeignKey("professional_profiles.id"),
        nullable=False
    )

    # Service being booked
    service_id = db.Column(
        db.Integer,
        db.ForeignKey("services.id"),
        nullable=False
    )

    # Date selected through the availability slot
    preferred_date = db.Column(
        db.Date,
        nullable=False
    )

    # Time selected through the availability slot
    preferred_time = db.Column(
        db.Time,
        nullable=True
    )

    # Availability slot selected by the user
    availability_slot_id = db.Column(
        db.Integer,
        db.ForeignKey("availability_slots.id"),
        nullable=True
    )

    availability_slot = db.relationship(
        "AvailabilitySlot",
        foreign_keys=[availability_slot_id],
        backref=db.backref(
            "service_requests",
            lazy=True
        )
    )

    # Old slot_id column currently present in database.
    # We are not using it for the new booking flow.
    slot_id = db.Column(
        db.Integer,
        nullable=True
    )

    # User's requirement
    description = db.Column(
        db.Text,
        nullable=False
    )

    # Location
    location = db.Column(
        db.String(200),
        nullable=True
    )

    # Additional information
    additional_details = db.Column(
        db.Text,
        nullable=True
    )

    # Booking status
    status = db.Column(
        db.String(30),
        nullable=False,
        default="pending"
    )

    # Payment status
    payment_status = db.Column(
        db.String(30),
        nullable=True,
        default="pending"
    )

    # Payment gateway transaction ID
    payment_id = db.Column(
        db.String(255),
        nullable=True
    )

    # Amount paid
    payment_amount = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )
        # Refund status
    refund_status = db.Column(
        db.String(30),
        nullable=True,
        default="not_required"
    )

    # Amount refunded
    refund_amount = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )

    # Refund transaction ID
    refund_id = db.Column(
        db.String(255),
        nullable=True
    )
    
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships

    user = db.relationship(
        "User",
        backref=db.backref(
            "service_requests",
            lazy=True
        )
    )

    professional = db.relationship(
        "ProfessionalProfile",
        backref=db.backref(
            "service_requests",
            lazy=True
        )
    )

    service = db.relationship(
        "Service",
        backref=db.backref(
            "service_requests",
            lazy=True
        )
    )

    def __repr__(self):
        return f"<ServiceRequest {self.id}>"