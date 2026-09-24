from datetime import datetime

from ..extensions import db
from ..utils.email import send_email
from ..models.professional_service_request import ProfessionalServiceRequest


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    notification_type = db.Column(
        db.String(50),
        nullable=False
    )

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("service_requests.id"),
        nullable=True
    )

    professional_service_request_id = db.Column(
        db.Integer,
        db.ForeignKey("professional_service_requests.id"),
        nullable=True
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref(
            "notifications",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    booking = db.relationship(
        "ServiceRequest",
        backref=db.backref(
            "notifications",
            lazy=True
        )
    )

    professional_service_request = db.relationship(
        "ProfessionalServiceRequest",
        backref=db.backref(
            "notifications",
            lazy=True
        )
    )
    professional_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    

    def __repr__(self):
        return f"<Notification {self.id}>"