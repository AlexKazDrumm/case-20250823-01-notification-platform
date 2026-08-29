from django.test import TestCase, override_settings
from notifications.models import Notification
from notifications.services import perform_delivery
import os

class FallbackTest(TestCase):
    def test_email_success(self):
        notif = Notification.objects.create(message="Hello", to_email="dev@example.com", channels_order=["email"])
        ok = perform_delivery(notif)
        self.assertTrue(ok)
        self.assertEqual(notif.status, "SENT")
        self.assertEqual(notif.attempts.count(), 1)

    def test_sms_fallback(self):
        os.environ["MOCK_SMS_MODE"] = "fail"
        notif = Notification.objects.create(message="Hi", to_phone="+79990000000", channels_order=["sms","email"])
        ok = perform_delivery(notif)
        self.assertTrue(ok)
        self.assertEqual(notif.status, "SENT")
        self.assertEqual(notif.attempts.count(), 2)
        self.assertEqual(notif.attempts.first().status, "FAILED")
        self.assertEqual(notif.attempts.last().status, "SUCCESS")
