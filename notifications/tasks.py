from celery import shared_task, states
from django.db import transaction
from .models import Notification
from .services import perform_delivery
import random

def _backoff(retries:int) -> int:
    base = 5
    delay = min(600, (2 ** retries) * base + random.randint(0, 5))
    return delay

@shared_task(bind=True, max_retries=5, default_retry_delay=5)
def send_notification_task(self, notification_id: int, attachments=None, force_channel: str | None = None):
    try:
        notif = Notification.objects.get(pk=notification_id)
        if force_channel is None and notif.attempts.filter(status="SUCCESS").exists():
            return "skipped: already SUCCESS"

        if force_channel is not None and notif.attempts.filter(channel=force_channel, status="SUCCESS").exists():
            return f"skipped: {force_channel} already SUCCESS"

        with transaction.atomic():
            ok = perform_delivery(notif, attachments=attachments, force_channel=force_channel)
            return "ok" if ok else "failed"
    except Notification.DoesNotExist:
        return "Notification missing"
    except Exception as exc:
        delay = _backoff(self.request.retries)
        raise self.retry(exc=exc, countdown=delay)

@shared_task(bind=True, max_retries=3)
def send_via_channel(self, notification_id: int, channel: str, attachments=None):
    return send_notification_task.apply_async(kwargs={"notification_id": notification_id, "attachments": attachments, "force_channel": channel})
