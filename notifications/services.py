from django.db.models import Max
from django.conf import settings
from .models import Notification, DeliveryAttempt
from .providers.email import send_email
from .providers.sms import send_sms
from .providers.telegram import send_telegram

CHANNEL_SENDERS = {
    "email": lambda n, attachments=None: send_email(n.subject or "", n.message, n.to_email or "", attachments=attachments),
    "sms": lambda n, attachments=None: send_sms(n.message, n.to_phone or ""),
    "telegram": lambda n, attachments=None: send_telegram(
        n.message,
        (n.to_telegram_chat_id or n.to_telegram or n.to_telegram_username or "")
    ),
}

def _iter_orders(order: list[str]):
    if not order:
        return
    yield order
    if getattr(settings, "SECOND_PASS_ENABLED", True) and len(order) > 1:
        rotated = order[1:] + order[:1]
        if rotated != order:
            yield rotated

def perform_delivery(notification: Notification, attachments=None, force_channel: str | None = None) -> bool:
    any_success = False

    order = notification.channels_order or settings.DEFAULT_CHANNELS_ORDER
    passes = list(_iter_orders(order))
    if force_channel:
        passes = [[force_channel]]

    start_no = notification.attempts.aggregate(m=Max("attempt_no")).get("m") or 0
    attempt_no = start_no

    for current in passes:
        for channel in current:
            attempt_no += 1
            attempt = DeliveryAttempt.objects.create(
                notification=notification, channel=channel, attempt_no=attempt_no, status="PENDING"
            )
            sender = CHANNEL_SENDERS.get(channel)
            if not sender:
                attempt.status = "FAILED"
                attempt.error = "Unknown channel"
                attempt.save(update_fields=["status", "error"])
                continue

            result = sender(notification, attachments=attachments)
            if result.ok:
                attempt.status = "SUCCESS"
                attempt.provider_message_id = result.message_id
                attempt.save(update_fields=["status", "provider_message_id"])
                any_success = True
                break
            else:
                attempt.status = "FAILED"
                attempt.error = result.error
                attempt.save(update_fields=["status", "error"])
                continue
        if any_success:
            break

    notification.status = "SENT" if any_success else "FAILED"
    notification.save(update_fields=["status"])
    return any_success
