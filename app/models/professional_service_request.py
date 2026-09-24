from datetime import datetime
from ..extensions import db
from sqlalchemy import UniqueConstraint


class ProfessionalServiceRequest(db.Model):
    __tablename__ = "professional_service_requests"

    id = db.Column(db.Integer, primary_key=True)

    professional_id = db.Column(
        db.Integer,
        db.ForeignKey("professional_profiles.id"),
        nullable=False
    )

    service_id = db.Column(
        db.Integer,
        db.ForeignKey("services.id"),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
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

    professional = db.relationship(
        "ProfessionalProfile",
        backref=db.backref(
            "professional_service_requests",
            lazy=True
        )
    )

    service = db.relationship(
        "Service",
        backref=db.backref(
            "professional_service_requests",
            lazy=True
        )
    )

    __table_args__ = (
        UniqueConstraint(
            "professional_id",
            "service_id",
            name="uq_professional_service_request"
        ),
    )

    def __repr__(self):
        return (
            f"<ProfessionalServiceRequest "
            f"{self.professional_id} "
            f"{self.service_id} "
            f"{self.status}>"
        )