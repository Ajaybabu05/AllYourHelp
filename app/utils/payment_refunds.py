
import razorpay
from flask import current_app
from ..models.payment_refund import PaymentRefund
from ..extensions import db


def process_full_refund(payment):
    """Request a full Razorpay refund and record the returned refund details."""

    if not payment:
        return False, "Payment record not found.", None, None

    if payment.status == "refunded":
        return False, "This payment has already been refunded.", None, None

    if payment.refund_id and payment.status == "paid":
        return False, "A refund request is already pending or needs review.", None, None

    if payment.status != "paid":
        return False, "Only paid payments can be refunded.", None, None

    if payment.gateway != "razorpay":
        return False, "This payment was not processed through Razorpay.", None, None

    if not payment.gateway_payment_id:
        return False, "Razorpay payment ID is missing.", None, None

    key_id = current_app.config.get("RAZORPAY_KEY_ID")
    key_secret = current_app.config.get("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        current_app.logger.error("Razorpay credentials are not configured.")
        return False, "Refund service is not configured.", None, None

    try:
        client = razorpay.Client(auth=(key_id, key_secret))

        refund = client.payment.refund(
            payment.gateway_payment_id,
            {"amount": int(round(float(payment.amount) * 100))}
        )

        refund_id = refund.get("id")
        refund_status = refund.get("status")

        if not refund_id or refund_status not in ("processed", "pending"):
            return False, "Razorpay has not accepted the refund.", None, refund_status

        refund_record = PaymentRefund.query.filter_by(
            razorpay_refund_id=refund_id
        ).first()
        if refund_record and refund_record.payment_id != payment.id:
            current_app.logger.error(
                "Razorpay refund ID %s is already linked to another payment.",
                refund_id
            )
            return False, "Refund record verification failed.", None, None

        if refund_record is None:
            refund_record = PaymentRefund(
                payment_id=payment.id,
                razorpay_refund_id=refund_id,
                amount=round(float(payment.amount), 2),
                status=refund_status
            )
            db.session.add(refund_record)

        elif refund_record.status == "processed":
            current_app.logger.warning(
                "Razorpay returned an existing processed refund ID %s "
                "for payment %s.",
                refund_id,
                payment.id
            )
            return (
                False,
                "This refund has already been processed. "
                "Please verify the payment before retrying.",
                None,
                refund_status
            )

        else:
            refund_record.amount = round(float(payment.amount), 2)
            refund_record.status = refund_status

        # The calling route is responsible for committing database changes.

        return True, "Refund request accepted.", refund_id, refund_status

    except Exception:
        current_app.logger.exception(
            "Razorpay refund request failed for payment %s.",
            payment.id
        )
        return False, "Refund request failed. Please try again later.", None, None
