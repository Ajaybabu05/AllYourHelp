from datetime import datetime

from ..extensions import db


class AdminSettings(db.Model):
    __tablename__ = "admin_settings"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    site_name = db.Column(
        db.String(100),
        nullable=False,
        default="AllYourHelp"
    )

    support_email = db.Column(
        db.String(255),
        nullable=True
    )

    support_phone = db.Column(
        db.String(30),
        nullable=True
    )

    maintenance_mode = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    bookings_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    payments_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    email_notifications_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    platform_fee_percentage = db.Column(
        db.Numeric(5, 2),
        nullable=False,
        default=0
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

    def __repr__(self):
        return f"<AdminSettings {self.id}>"