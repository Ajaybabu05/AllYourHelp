from ..extensions import db


professional_services = db.Table(
    "professional_services",

    db.Column(
        "professional_id",
        db.Integer,
        db.ForeignKey("professional_profiles.id"),
        primary_key=True
    ),

    db.Column(
        "service_id",
        db.Integer,
        db.ForeignKey("services.id"),
        primary_key=True
    )
)


class ProfessionalProfile(db.Model):

    __tablename__ = "professional_profiles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True
    )

    bio = db.Column(
        db.Text,
        nullable=True
    )

    experience = db.Column(
        db.Integer,
        nullable=True
    )

    location = db.Column(
        db.String(150),
        nullable=True
    )

    is_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    user = db.relationship(
        "User",
        back_populates="professional_profile"
    )

    services = db.relationship(
        "Service",
        secondary=professional_services,
        back_populates="professionals"
    )

    def __repr__(self):
        return f"<ProfessionalProfile {self.id}>"