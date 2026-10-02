from datetime import datetime

from ..extensions import db


class Payment(db.Model):

    __tablename__ = "payments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ---------------------------------------------------------
    # BOOKING
    # ---------------------------------------------------------

    service_request_id = db.Column(
        db.Integer,
        db.ForeignKey("service_requests.id"),
        nullable=True,
        unique=True
    )

    service_request = db.relationship(
        "ServiceRequest",
        backref=db.backref(
            "payment",
            uselist=False
        )
    )

    # ---------------------------------------------------------
    # CUSTOMER
    # ---------------------------------------------------------

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "payments",
            lazy=True
        )
    )

    # ---------------------------------------------------------
    # PROFESSIONAL
    # ---------------------------------------------------------

    professional_id = db.Column(
        db.Integer,
        db.ForeignKey("professional_profiles.id"),
        nullable=False
    )

    professional = db.relationship(
        "ProfessionalProfile",
        backref=db.backref(
            "payments",
            lazy=True
        )
    )

    # ---------------------------------------------------------
    # PAYMENT AMOUNT
    # ---------------------------------------------------------

    amount = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    currency = db.Column(
        db.String(10),
        nullable=False,
        default="INR"
    )

    # ---------------------------------------------------------
    # PAYMENT STATUS
    # ---------------------------------------------------------

    status = db.Column(
        db.String(30),
        nullable=False,
        default="pending"
    )

    # Possible values:
    #
    # pending
    # paid
    # failed
    # cancelled
    # refunded
    #
    # We will use these when integrating Razorpay.

    # ---------------------------------------------------------
    # PAYMENT GATEWAY
    # ---------------------------------------------------------

    gateway = db.Column(
        db.String(50),
        nullable=True
    )

    # Example:
    # razorpay

    # ---------------------------------------------------------
    # GATEWAY ORDER ID
    # ---------------------------------------------------------

    gateway_order_id = db.Column(
        db.String(255),
        nullable=True,
        unique=True
    )

    # Example:
    # order_xxxxxxxxxx

    # ---------------------------------------------------------
    # GATEWAY PAYMENT ID
    # ---------------------------------------------------------

    gateway_payment_id = db.Column(
        db.String(255),
        nullable=True,
        unique=True
    )

    # Example:
    # pay_xxxxxxxxxx

    # ---------------------------------------------------------
    # PAYMENT SIGNATURE
    # ---------------------------------------------------------

    gateway_signature = db.Column(
        db.String(500),
        nullable=True
    )

    # Used for server-side payment verification.

    # ---------------------------------------------------------
    # PAYMENT TIME
    # ---------------------------------------------------------

    paid_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # ---------------------------------------------------------
    # FAILURE INFORMATION
    # ---------------------------------------------------------

    failure_reason = db.Column(
        db.Text,
        nullable=True
    )

    # ---------------------------------------------------------
    # REFUND INFORMATION
    # ---------------------------------------------------------

    refund_id = db.Column(
        db.String(255),
        nullable=True
    )

    refund_amount = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )

    refunded_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # ---------------------------------------------------------
    # TIMESTAMPS
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # REPRESENTATION
    # ---------------------------------------------------------

    def __repr__(self):

        return (
            f"<Payment "
            f"id={self.id} "
            f"booking_id={self.service_request_id} "
            f"status='{self.status}'>"
        )