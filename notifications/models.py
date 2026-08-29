from django.db import models
from django.contrib.postgres.fields import ArrayField

class Notification(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SENT", "Sent"),
        ("FAILED", "Failed"),
        ("DELIVERED","Delivered"),
        ("BOUNCED","Bounced"),
    ]
    subject = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField()
    to_email = models.EmailField(blank=True, null=True)
    to_phone = models.CharField(max_length=32, blank=True, null=True)
    to_telegram = models.CharField(max_length=64, blank=True, null=True)
    to_telegram_username = models.CharField(max_length=64, blank=True, null=True)
    to_telegram_chat_id = models.CharField(max_length=32, blank=True, null=True)
    channels_order = models.JSONField(default=list)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification #{self.pk} [{self.status}]"

class DeliveryAttempt(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("DELIVERED","Delivered"),
        ("BOUNCED","Bounced"),
    ]
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="attempts")
    channel = models.CharField(max_length=16)  # email | sms | telegram
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="PENDING")
    error = models.TextField(blank=True, null=True)
    attempt_no = models.PositiveIntegerField(default=1)
    provider_message_id = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["attempt_no", "created_at"]

    def __str__(self):
        return f"{self.channel} attempt {self.attempt_no} for notif {self.notification_id}"


class IdempotencyKey(models.Model):
    key = models.CharField(max_length=128, unique=True)
    request_hash = models.CharField(max_length=64)
    notification = models.ForeignKey(Notification, on_delete=models.SET_NULL, null=True, blank=True)
    response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.key
