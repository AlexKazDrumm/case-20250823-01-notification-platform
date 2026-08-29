from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from notifications.models import Notification
from notifications.serializers import NotificationCreateSerializer
from notifications.tasks import send_notification_task
from notifications.services import perform_delivery
from .forms import NotificationCreateForm
from django.contrib.auth import get_user_model

User = get_user_model()
staff_required = user_passes_test(lambda u: u.is_active and u.is_staff)

@login_required
def home(request):
    return redirect("dashboard:notifications_list")

@login_required
def notifications_list(request):
    qs = Notification.objects.all().order_by("-created_at")
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/notifications_list.html", {"page": page})

@login_required
def users_list(request):
    qs = User.objects.all().order_by("username")
    paginator = Paginator(qs, 30)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/users_list.html", {"page": page})

@login_required
def notification_detail(request, pk: int):
    notif = get_object_or_404(Notification, pk=pk)
    attempts = notif.attempts.all().order_by("attempt_no","created_at")
    return render(request, "dashboard/notification_detail.html", {"notif": notif, "attempts": attempts})

@login_required
@staff_required
def notification_create(request):
    if request.method == "POST":
        form = NotificationCreateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            channels_order = data.get("channels_order") or None
            created_ids = []

            try:
                with transaction.atomic():
                    to = {}
                    if data.get("to_email"):
                        to["email"] = data["to_email"]
                    if data.get("to_phone"):
                        to["phone"] = data["to_phone"]
                    if data.get("to_telegram"):
                        to["telegram_chat_id"] = data["to_telegram"]

                    if to:
                        s = NotificationCreateSerializer(data={
                            "subject": data.get("subject"),
                            "message": data["message"],
                            "to": to,
                            "channels_order": channels_order
                        })
                        s.is_valid(raise_exception=True)
                        notif = s.save()
                        created_ids.append(notif.id)

                    users = data.get("users")
                    if users:
                        for u in users:
                            uto = {
                                "email": u.email or None,
                                "phone": getattr(u, "phone", None),
                            }

                            tg_id = getattr(u, "telegram_chat_id", None)
                            tg_username = getattr(u, "telegram_username", None)
                            if tg_id:
                                uto["telegram_chat_id"] = tg_id
                            elif tg_username:
                                uto["telegram_username"] = tg_username

                            if not any(uto.values()):
                                continue

                            s2 = NotificationCreateSerializer(data={
                                "subject": data.get("subject"),
                                "message": data["message"],
                                "to": uto,
                                "channels_order": channels_order
                            })
                            s2.is_valid(raise_exception=True)
                            n2 = s2.save()
                            created_ids.append(n2.id)
            except Exception as e:
                messages.error(request, f"Ошибка создания уведомления: {e}")
                return render(request, "dashboard/notification_create.html", {"form": form})

            mode = data.get("mode")
            channel = data.get("channel")

            for nid in created_ids:
                notif = Notification.objects.get(pk=nid)
                if mode == "channel" and channel:
                    send_notification_task.delay(notif.id, force_channel=channel)
                else:
                    send_notification_task.delay(notif.id)

            messages.success(request, f"Создано уведомлений: {len(created_ids)}")
            return redirect("dashboard:notifications_list")
    else:
        form = NotificationCreateForm()

    return render(request, "dashboard/notification_create.html", {"form": form})

@login_required
@staff_required
def notification_resend(request, pk: int):
    notif = get_object_or_404(Notification, pk=pk)
    if request.method == "POST":
        mode = request.POST.get("mode", "chain")
        channel = request.POST.get("channel") or None

        from notifications.tasks import send_notification_task
        if mode == "channel" and channel:
            send_notification_task.delay(notif.id, force_channel=channel)
            messages.info(request, f"Переотправка через канал: {channel}")
        else:
            send_notification_task.delay(notif.id)
            messages.info(request, "Переотправка по цепочке")

        return redirect("dashboard:notification_detail", pk=pk)
    return render(request, "dashboard/notification_resend.html", {"notif": notif})