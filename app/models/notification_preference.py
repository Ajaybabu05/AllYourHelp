from ..extensions import db


class NotificationPreference(db.Model):
    __tablename__ = "notification_preferences"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    booking_confirmation = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    booking_updates = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    professional_responses = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    completion_reminders = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "notification_preferences",
            uselist=False
        )
    )

    def __repr__(self):
        return f"<NotificationPreference user_id={self.user_id}>"