
from datetime import datetime

from ..extensions import db


class PaymentRefund(db.Model):
    __tablename__ = "payment_refunds"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    payment_id = db.Column(
        db.Integer,
        db.ForeignKey("payments.id"),
        nullable=False,
        index=True
    )

    razorpay_refund_id = db.Column(
        db.String(255),
        nullable=False,
        unique=True
    )

    amount = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    payment = db.relationship(
        "Payment",
        backref=db.backref(
            "refunds",
            lazy=True
        )
    )

    def __repr__(self):
        return (
            f"<PaymentRefund "
            f"id={self.id} "
            f"payment_id={self.payment_id} "
            f"status='{self.status}'>"
        )
