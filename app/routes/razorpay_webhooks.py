
import hashlib
import hmac

from flask import Blueprint, request, current_app
from ..extensions import db, csrf
from ..models.payment import Payment
from ..models.service_request import ServiceRequest
from ..models.payment_refund import PaymentRefund
from datetime import datetime


razorpay_webhooks = Blueprint(
    "razorpay_webhooks",
    __name__,
    url_prefix="/webhooks"
)

@razorpay_webhooks.route("/razorpay", methods=["POST"])
@csrf.exempt
def razorpay_webhook():
    webhook_secret = current_app.config.get(
        "RAZORPAY_WEBHOOK_SECRET"
    )

    if not webhook_secret:
        current_app.logger.error(
            "Razorpay webhook secret is not configured."
        )
        return {"error": "Webhook is not configured"}, 500

    signature = request.headers.get(
        "X-Razorpay-Signature", ""
    )
    payload = request.get_data()

    expected_signature = hmac.new(
        webhook_secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not signature or not hmac.compare_digest(
        expected_signature, signature
    ):
        return {"error": "Invalid signature"}, 400

    try:
        event_data = request.get_json()
    except Exception:
        return {"error": "Invalid JSON"}, 400

    if not isinstance(event_data, dict):
        return {"error": "Invalid payload"}, 400

    event = event_data.get("event")

    if event not in ("refund.processed", "refund.failed"):
        return {"status": "ignored"}, 200

    payload_data = event_data.get("payload") or {}
    refund_data = payload_data.get("refund") or {}
    refund = refund_data.get("entity") or {}

    refund_id = refund.get("id")
    refund_status = refund.get("status")
    refund_amount_paise = refund.get("amount")
    refund_payment_id = refund.get("payment_id")

    if not refund_id:
        current_app.logger.warning(
            "Razorpay refund webhook has no refund ID."
        )
        return {"error": "Missing refund ID"}, 400

    if not refund_payment_id:
        current_app.logger.warning(
            "Razorpay refund %s has no payment ID.",
            refund_id
        )
        return {"error": "Missing payment ID"}, 400

    payment = Payment.query.filter_by(
        gateway_payment_id=refund_payment_id,
        gateway="razorpay"
    ).with_for_update().first()

    if not payment:
        current_app.logger.warning(
            "No payment found for Razorpay payment ID %s.",
            refund_payment_id
        )
        return {"status": "payment_not_found"}, 200

    service_request = None

    if payment.service_request_id:
        service_request = db.session.get(
            ServiceRequest,
            payment.service_request_id
        )
    refund_record = PaymentRefund.query.filter_by(
        razorpay_refund_id=refund_id
    ).first()

    if refund_record and refund_record.payment_id != payment.id:
        current_app.logger.error(
            "Refund ID %s is linked to a different payment.",
            refund_id
        )
        return {"error": "Refund record mismatch"}, 400

    
    if event == "refund.processed":
        # A refund record may already be marked processed by the helper.
        # Recalculate the payment totals below before deciding whether
        # this webhook has already been fully applied.

        if refund_status != "processed":
            return {"status": "awaiting_confirmation"}, 200

        if refund_amount_paise is None:
            current_app.logger.error(
                "Razorpay refund %s has no amount.",
                refund_id
            )
            return {"error": "Missing refund amount"}, 400

        try:
            refund_amount_rupees = int(refund_amount_paise) / 100
        except (TypeError, ValueError):
            return {"error": "Invalid refund amount"}, 400

        if refund_amount_rupees <= 0:
            return {"error": "Invalid refund amount"}, 400

        if round(refund_amount_rupees, 2) != round(
            float(payment.amount), 2
        ):
            current_app.logger.error(
                "Refund amount does not match the full payment amount "
                "for payment %s.",
                payment.id
            )
            return {
                "error": "Only full refunds are supported"
            }, 400

        # Check whether this refund would exceed the original payment amount.
        
        # Calculate refunds already processed, excluding this refund.
        already_refunded = sum(
            (
                float(item.amount)
                for item in payment.refunds
                if item.status == "processed"
                and item.razorpay_refund_id != refund_id
            ),
            start=0.0
        )

        # Do not allow the cumulative total to exceed the payment amount.
        if already_refunded + refund_amount_rupees > float(payment.amount):
            current_app.logger.error(
                "Cumulative refunds exceed payment amount for payment %s.",
                payment.id
            )
            return {
                "error": "Refund amount exceeds remaining payment amount"
            }, 400


        # Create or update the record for this individual refund.
        if refund_record is None:
            refund_record = PaymentRefund(
                payment_id=payment.id,
                razorpay_refund_id=refund_id,
                amount=refund_amount_rupees,
                status="processed"
            )
            db.session.add(refund_record)
        else:
            refund_record.amount = refund_amount_rupees
            refund_record.status = "processed"

        db.session.flush()

        # Calculate the total from all successfully processed refund records.
        total_refunded = sum(
            (
                float(item.amount)
                for item in payment.refunds
                if item.status == "processed"
            ),
            start=0.0
        )

        payment.refund_amount = total_refunded

        # Update the overall payment status using the cumulative total.
        
        if total_refunded == round(float(payment.amount), 2):
            payment.status = "refunded"
            payment.refunded_at = datetime.utcnow()
        elif total_refunded < round(float(payment.amount), 2):
            payment.status = "partially_refunded"
            payment.refunded_at = None
        else:
            current_app.logger.error(
                "Refund total exceeds payment amount for payment %s.",
                payment.id
            )
            db.session.rollback()
            return {"error": "Refund total exceeds payment amount"}, 400


        if service_request:
            service_request.refund_status = payment.status
            service_request.refund_id = refund_id
            service_request.payment_status = payment.status
            service_request.refund_amount = total_refunded
            if payment.status == "refunded" and service_request.refund_action == "cancel":
                if service_request.status in ("pending", "confirmed"):
                    service_request.status = "cancelled"

                    if service_request.availability_slot:
                        service_request.availability_slot.is_booked = False

                service_request.refund_action = None


    elif event == "refund.failed":
        if refund_record and refund_record.status == "processed":
            current_app.logger.warning(
                "Ignoring failed webhook for already processed refund %s.",
                refund_id
            )
            return {"status": "already_processed"}, 200
        if refund_status != "failed":
            return {"status": "awaiting_confirmation"}, 200

        if refund_amount_paise is None:
            return {"error": "Missing refund amount"}, 400

        try:
            failed_amount = int(refund_amount_paise) / 100
        except (TypeError, ValueError):
            return {"error": "Invalid refund amount"}, 400

        if failed_amount <= 0:
            return {"error": "Invalid refund amount"}, 400

        if refund_record is None:
            refund_record = PaymentRefund(
                payment_id=payment.id,
                razorpay_refund_id=refund_id,
                amount=failed_amount,
                status="failed"
            )
            db.session.add(refund_record)
        else:
            refund_record.amount = failed_amount
            refund_record.status = "failed"

        
        if service_request:
            service_request.refund_status = "failed"
            service_request.refund_id = refund_id
            if service_request.refund_action == "cancel":
                service_request.refund_action = None


        current_app.logger.error(
            "Refund failed for payment %s. Refund ID: %s",
            payment.id,
            refund_id
        )



    db.session.commit()

    return {"status": "processed"}, 200

