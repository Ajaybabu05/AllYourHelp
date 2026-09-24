from ..extensions import db


class ServiceCategory(db.Model):

    __tablename__ = "service_categories"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    slug = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    services = db.relationship(
        "Service",
        back_populates="category",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ServiceCategory {self.name}>"