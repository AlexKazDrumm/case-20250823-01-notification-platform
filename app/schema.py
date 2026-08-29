import datetime as dt
from typing import Optional, List

import strawberry
from notifications.models import Notification, DeliveryAttempt
from notifications.serializers import NotificationCreateSerializer


@strawberry.type
class AttemptType:
    id: int
    channel: str
    status: str
    error: Optional[str]
    attempt_no: int
    created_at: dt.datetime


@strawberry.type
class NotificationType:
    id: int
    subject: Optional[str]
    message: str
    status: str
    channels_order: List[str]
    to_email: Optional[str]
    to_phone: Optional[str]
    to_telegram: Optional[str]
    to_telegram_username: Optional[str]
    to_telegram_chat_id: Optional[str]
    created_at: dt.datetime
    updated_at: dt.datetime

    @strawberry.field
    def attempts(self) -> List[AttemptType]:
        ats = DeliveryAttempt.objects.filter(notification_id=self.id).order_by("attempt_no", "created_at")
        return [
            AttemptType(
                id=a.id,
                channel=a.channel,
                status=a.status,
                error=a.error,
                attempt_no=a.attempt_no,
                created_at=a.created_at,
            )
            for a in ats
        ]


def notif_to_type(n: Notification) -> NotificationType:
    return NotificationType(
        id=n.id,
        subject=n.subject,
        message=n.message,
        status=n.status,
        channels_order=list(n.channels_order or []),
        to_email=n.to_email,
        to_phone=n.to_phone,
        to_telegram=n.to_telegram,
        created_at=n.created_at,
        updated_at=n.updated_at,
    )


@strawberry.type
class Query:
    @strawberry.field
    def notification(self, id: int) -> Optional[NotificationType]:
        n = Notification.objects.filter(pk=id).first()
        return notif_to_type(n) if n else None

    @strawberry.field
    def attempts(self, notification_id: int) -> List[AttemptType]:
        ats = DeliveryAttempt.objects.filter(notification_id=notification_id).order_by("attempt_no", "created_at")
        return [
            AttemptType(
                id=a.id,
                channel=a.channel,
                status=a.status,
                error=a.error,
                attempt_no=a.attempt_no,
                created_at=a.created_at,
            )
            for a in ats
        ]


@strawberry.input
class RecipientInput:
    email: Optional[str] = None
    phone: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_username: Optional[str] = None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_notification(
        self,
        subject: Optional[str],
        message: str,
        recipient: RecipientInput,
        channels_order: Optional[List[str]] = None,
    ) -> NotificationType:
        data = {
            "subject": subject,
            "message": message,
            "to": {
                "email": recipient.email,
                "phone": recipient.phone,
                "telegram_chat_id": recipient.telegram_chat_id,
                "telegram_username": recipient.telegram_username,
            },
            "channels_order": channels_order,
        }
        s = NotificationCreateSerializer(data=data)
        s.is_valid(raise_exception=True)
        instance = s.save()
        return notif_to_type(instance)


schema = strawberry.Schema(query=Query, mutation=Mutation)
