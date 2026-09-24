from datetime import datetime

from ..extensions import db


class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    professional_id = db.Column(
        db.Integer,
        db.ForeignKey("professional_profiles.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "favorites",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    professional = db.relationship(
        "ProfessionalProfile",
        backref=db.backref(
            "favorited_by",
            lazy=True
        )
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "professional_id",
            name="unique_user_professional_favorite"
        ),
    )

    def __repr__(self):
        return f"<Favorite {self.id}>"