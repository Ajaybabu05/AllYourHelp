from datetime import datetime

from ..extensions import db


class AdminActivityLog(db.Model):
    __tablename__ = "admin_activity_logs"

    id = db.Column(db.Integer, primary_key=True)

    admin_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    action = db.Column(
        db.String(100),
        nullable=False
    )

    target_type = db.Column(
        db.String(50),
        nullable=True
    )

    target_id = db.Column(
        db.Integer,
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    ip_address = db.Column(
        db.String(45),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    admin = db.relationship(
        "User",
        backref=db.backref(
            "activity_logs",
            lazy=True
        )
    )

    def __repr__(self):
        return (
            f"<AdminActivityLog "
            f"id={self.id} "
            f"admin_id={self.admin_id} "
            f"action='{self.action}'>"
        )