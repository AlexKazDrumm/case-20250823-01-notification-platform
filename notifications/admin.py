from django.contrib import admin
from .models import Notification, DeliveryAttempt

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "status", "to_email", "to_phone", "to_telegram", "created_at")
    search_fields = ("subject", "message", "to_email", "to_phone", "to_telegram")
    list_filter = ("status", "created_at")

@admin.register(DeliveryAttempt)
class DeliveryAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "notification", "channel", "status", "attempt_no", "created_at")
    list_filter = ("channel", "status")
