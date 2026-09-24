from ..extensions import db


class Service(db.Model):

    __tablename__ = "services"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "service_categories.id"
        ),
        nullable=False
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    slug = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    price = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    category = db.relationship(
        "ServiceCategory",
        back_populates="services"
    )

    professionals = db.relationship(
        "ProfessionalProfile",
        secondary="professional_services",
        back_populates="services"
    )

    def __repr__(self):
        return f"<Service {self.name}>"