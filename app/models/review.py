from datetime import datetime

from ..extensions import db


class Review(db.Model):

    __tablename__ = "reviews"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # User who submitted the review
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Professional being reviewed
    professional_id = db.Column(
        db.Integer,
        db.ForeignKey("professional_profiles.id"),
        nullable=False
    )

    # Booking associated with this review
    service_request_id = db.Column(
        db.Integer,
        db.ForeignKey("service_requests.id"),
        nullable=False,
        unique=True
    )

    # Rating from 1 to 5
    rating = db.Column(
        db.Integer,
        nullable=False
    )

    # Written review
    comment = db.Column(
        db.Text,
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
            "reviews",
            lazy=True
        )
    )

    professional = db.relationship(
        "ProfessionalProfile",
        backref=db.backref(
            "reviews",
            lazy=True
        )
    )

    service_request = db.relationship(
        "ServiceRequest",
        backref=db.backref(
            "review",
            uselist=False
        )
    )

    def __repr__(self):
        return f"<Review {self.id}>"