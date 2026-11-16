
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import create_app


class RefundSafetyTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True

    def test_processed_refund_response_is_recorded_safely(self):
        with self.app.app_context():
            payment = SimpleNamespace(
                id=1,
                status="paid",
                gateway="razorpay",
                gateway_payment_id="pay_test_123",
                refund_id=None,
                amount=100.00,
            )

            fake_refund = {
                "id": "rfnd_test_123",
                "status": "processed",
            }

            with (
                patch(
                    "app.utils.payment_refunds.razorpay.Client"
                ) as mock_client,
                patch(
                    "app.utils.payment_refunds.PaymentRefund.query"
                ) as mock_query,
                patch(
                    "app.utils.payment_refunds.db.session.add"
                ) as mock_add,
            ):
                mock_client.return_value.payment.refund.return_value = (
                    fake_refund
                )
                mock_query.filter_by.return_value.first.return_value = None

                from app.utils.payment_refunds import process_full_refund

                success, message, refund_id, refund_status = (
                    process_full_refund(payment)
                )

                self.assertTrue(success)
                self.assertEqual(refund_id, "rfnd_test_123")
                self.assertEqual(refund_status, "processed")
                self.assertEqual(payment.status, "paid")
                mock_add.assert_called_once()

                mock_client.return_value.payment.refund.assert_called_once_with(
                    "pay_test_123",
                    {"amount": 10000},
                )

    
    def test_pending_refund_does_not_mark_payment_as_refunded(self):
        with self.app.app_context():
            payment = SimpleNamespace(
                id=2,
                status="paid",
                gateway="razorpay",
                gateway_payment_id="pay_test_pending",
                refund_id=None,
                amount=250.00,
            )

            fake_refund = {
                "id": "rfnd_test_pending",
                "status": "pending",
            }

            with (
                patch(
                    "app.utils.payment_refunds.razorpay.Client"
                ) as mock_client,
                patch(
                    "app.utils.payment_refunds.PaymentRefund.query"
                ) as mock_query,
                patch(
                    "app.utils.payment_refunds.db.session.add"
                ) as mock_add,
            ):
                mock_client.return_value.payment.refund.return_value = (
                    fake_refund
                )
                mock_query.filter_by.return_value.first.return_value = None

                from app.utils.payment_refunds import process_full_refund

                success, message, refund_id, refund_status = (
                    process_full_refund(payment)
                )

                self.assertTrue(success)
                self.assertEqual(refund_id, "rfnd_test_pending")
                self.assertEqual(refund_status, "pending")
                self.assertEqual(payment.status, "paid")
                mock_add.assert_called_once()

    
    def test_razorpay_exception_does_not_mark_payment_as_refunded(self):
        with self.app.app_context():
            payment = SimpleNamespace(
                id=3,
                status="paid",
                gateway="razorpay",
                gateway_payment_id="pay_test_failure",
                refund_id=None,
                amount=150.00,
            )

            with patch(
                "app.utils.payment_refunds.razorpay.Client"
            ) as mock_client:
                mock_client.return_value.payment.refund.side_effect = (
                    Exception("Simulated Razorpay failure")
                )

                from app.utils.payment_refunds import process_full_refund

                success, message, refund_id, refund_status = (
                    process_full_refund(payment)
                )

                self.assertFalse(success)
                self.assertIsNone(refund_id)
                self.assertIsNone(refund_status)
                self.assertEqual(payment.status, "paid")

    
    def test_refund_without_id_is_rejected(self):
        with self.app.app_context():
            payment = SimpleNamespace(
                id=4,
                status="paid",
                gateway="razorpay",
                gateway_payment_id="pay_test_no_refund_id",
                refund_id=None,
                amount=200.00,
            )

            with patch(
                "app.utils.payment_refunds.razorpay.Client"
            ) as mock_client:
                mock_client.return_value.payment.refund.return_value = {
                    "status": "processed"
                }

                from app.utils.payment_refunds import process_full_refund

                success, message, refund_id, refund_status = (
                    process_full_refund(payment)
                )

                self.assertFalse(success)
                self.assertIsNone(refund_id)
                self.assertEqual(message, "Razorpay has not accepted the refund.")
                self.assertEqual(payment.status, "paid")

    
    def test_already_refunded_payment_is_rejected(self):
        with self.app.app_context():
            payment = SimpleNamespace(
                id=5,
                status="refunded",
                gateway="razorpay",
                gateway_payment_id="pay_test_already_refunded",
                refund_id="rfnd_test_existing",
                amount=100.00,
            )

            with patch(
                "app.utils.payment_refunds.razorpay.Client"
            ) as mock_client:
                from app.utils.payment_refunds import process_full_refund

                success, message, refund_id, refund_status = (
                    process_full_refund(payment)
                )

                self.assertFalse(success)
                self.assertEqual(
                    message,
                    "This payment has already been refunded.",
                )
                self.assertIsNone(refund_id)
                self.assertIsNone(refund_status)
                mock_client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
