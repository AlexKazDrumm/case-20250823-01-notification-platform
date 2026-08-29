from rest_framework import viewsets, mixins, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from .models import Notification
from .serializers import NotificationCreateSerializer, NotificationReadSerializer

User = get_user_model()

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)

class NotificationViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Notification.objects.all().order_by("-created_at").prefetch_related("attempts")
    serializer_class = NotificationReadSerializer

    def get_permissions(self):
        if self.action in ["create","resend","dispatch","send_now"]:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ["create"]:
            return NotificationCreateSerializer
        return NotificationReadSerializer

    @action(detail=True, methods=["post"])
    def resend(self, request, pk=None):
        notif = self.get_object()
        from .tasks import send_notification_task
        send_notification_task.delay(notif.id)
        return Response({"detail": "Enqueued"})

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def dispatch(self, request, pk=None):
        """Админ: запустить цепочку (mode=chain) или выбранный канал (mode=channel, channel=name)."""
        notif = self.get_object()
        mode = request.data.get("mode","chain")
        channel = request.data.get("channel")
        attachments = request.data.get("attachments")

        from .tasks import send_notification_task
        if mode == "channel":
            if not channel:
                return Response({"detail":"channel is required for mode=channel"}, status=status.HTTP_400_BAD_REQUEST)
            send_notification_task.delay(notif.id, attachments, force_channel=channel)
        else:
            send_notification_task.delay(notif.id, attachments)
        return Response({"detail":"Enqueued"})

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def send_now(self, request, pk=None):
        """Админ: синхронно выполнить отправку, вернуть сразу результат."""
        notif = self.get_object()
        channel = request.data.get("channel")
        attachments = request.data.get("attachments")
        from .services import perform_delivery
        ok = perform_delivery(notif, attachments=attachments, force_channel=channel)
        if ok:
            return Response({"detail":"Sent"})
        return Response({"detail":"Failed"}, status=status.HTTP_400_BAD_REQUEST)
