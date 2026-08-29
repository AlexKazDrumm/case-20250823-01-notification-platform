from rest_framework import serializers
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from hashlib import sha256
from .models import Notification, IdempotencyKey
import phonenumbers
from datetime import timedelta

User = get_user_model()

class AttachmentSerializer(serializers.Serializer):
    filename = serializers.CharField(required=False)
    content = serializers.CharField(required=False)
    content_type = serializers.CharField(required=False)
    s3_uri = serializers.CharField(required=False)

class RecipientSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    telegram_chat_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    telegram_username = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    user_ids = serializers.ListField(child=serializers.IntegerField(), required=False)

    def validate_phone(self, value):
        if not value:
            return value
        try:
            parsed = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError("Invalid phone number")
        except Exception:
            raise serializers.ValidationError("Invalid phone number")
        return value

class NotificationCreateSerializer(serializers.ModelSerializer):
    to = RecipientSerializer(write_only=True, required=False)
    channels_order = serializers.ListField(child=serializers.ChoiceField(choices=["email","sms","telegram"]), required=False)
    attachments = AttachmentSerializer(many=True, required=False)

    class Meta:
        model = Notification
        fields = ("id","subject","message","to","channels_order","attachments","status","created_at","updated_at")
        read_only_fields = ("id","status","created_at","updated_at")

    def _apply_user_scope(self, data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        to = data.get("to") or {}
        if user and not user.is_staff:
            to.setdefault("email", user.email or None)
            to.setdefault("phone", user.phone or None)
            to.setdefault("telegram_chat_id", getattr(user, "telegram_username", None))
        else:
            users_ids = to.get("user_ids") or []
            if users_ids:
                users = User.objects.filter(id__in=users_ids)
                for u in users:
                    if u.email:
                        to["email"] = u.email
                        break
                    if u.phone:
                        to["phone"] = u.phone
                        break
                    if getattr(u, "telegram_username", None):
                        to["telegram_chat_id"] = u.telegram_username
                        break
            data["to"] = to
        return data

    def _dedupe_key(self, payload: dict) -> str:
        blob = f"{payload.get('subject')}|{payload.get('message')}|{payload.get('to')}|{payload.get('channels_order')}"
        return sha256(blob.encode("utf-8")).hexdigest()

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data = self._apply_user_scope(validated_data)
        to = validated_data.pop("to", {}) or {}
        channels = validated_data.pop("channels_order", None) or settings.DEFAULT_CHANNELS_ORDER
        attachments = self.initial_data.get("attachments") or []

        tg_chat_id = to.get("telegram_chat_id") or None
        tg_username = to.get("telegram_username") or None

        if tg_chat_id and tg_chat_id.startswith("@"):
            tg_username, tg_chat_id = tg_chat_id, None

        idemp_key = None
        if request:
            key = request.headers.get("Idempotency-Key")
            if key:
                idemp_key, created = IdempotencyKey.objects.get_or_create(key=key, defaults={"request_hash":"", "response":{}})
                if not created and idemp_key.notification_id:
                    return idemp_key.notification

        dkey = self._dedupe_key({"subject": validated_data.get("subject"), "message": validated_data.get("message"), "to": to, "channels_order": channels})
        window = timezone.now() - timedelta(seconds=getattr(settings,"IDEMPOTENCY_WINDOW_SEC",3600))
        existing = Notification.objects.filter(created_at__gte=window, message=validated_data.get("message"), to_email=to.get("email") or None, to_phone=to.get("phone") or None, to_telegram=to.get("telegram_chat_id") or None).first()
        if existing:
            if idemp_key and not idemp_key.notification_id:
                idemp_key.notification = existing
                idemp_key.request_hash = dkey
                idemp_key.save(update_fields=["notification","request_hash"])
            return existing

        notif = Notification.objects.create(
            channels_order=channels,
            to_email=to.get("email") or None,
            to_phone=to.get("phone") or None,
            to_telegram=(tg_chat_id or tg_username or None),
            to_telegram_username=tg_username,
            to_telegram_chat_id=tg_chat_id,
            **validated_data
        )

        if idemp_key:
            idemp_key.notification = notif
            idemp_key.request_hash = dkey
            idemp_key.save(update_fields=["notification","request_hash"])
        return notif

class NotificationReadSerializer(serializers.ModelSerializer):
    attempts = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ("id","subject","message","to_email","to_phone","to_telegram","channels_order","status","created_at","updated_at","attempts")

    def get_attempts(self, obj):
        return [
            {"channel": a.channel, "status": a.status, "error": a.error, "attempt_no": a.attempt_no, "provider_message_id": a.provider_message_id}
            for a in obj.attempts.all().order_by("attempt_no")
        ]
