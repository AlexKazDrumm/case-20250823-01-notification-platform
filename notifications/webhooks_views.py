import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.utils import timezone
from .models import DeliveryAttempt
from django.db.models import Q

@csrf_exempt
def ses_sns(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("invalid json")

    msg_type = payload.get("Type")
    if msg_type == "SubscriptionConfirmation":
        return JsonResponse({"ok": True})
    if msg_type != "Notification":
        return JsonResponse({"ok": True})

    msg = payload.get("Message")
    try:
        data = json.loads(msg)
    except Exception:
        data = {}

    event_type = data.get("notificationType")
    mail = data.get("mail", {})
    message_id = mail.get("messageId")

    attempts = DeliveryAttempt.objects.filter(provider_message_id=message_id)
    if not attempts.exists():
        return JsonResponse({"ok": True, "detail":"attempt not found"})

    if event_type == "Delivery":
        attempts.update(status="DELIVERED")
    elif event_type in ("Bounce","Complaint"):
        attempts.update(status="BOUNCED")
    return JsonResponse({"ok": True})

@csrf_exempt
def twilio_sms(request):
    message_id = request.POST.get("MessageSid")
    status = request.POST.get("MessageStatus","").lower()
    if not message_id:
        return HttpResponseBadRequest("missing MessageSid")

    qs = DeliveryAttempt.objects.filter(provider_message_id=message_id)
    if not qs.exists():
        return JsonResponse({"ok": True, "detail":"attempt not found"})

    if status in ("delivered","sent"):
        qs.update(status="DELIVERED")
    elif status in ("failed","undelivered","bounced"):
        qs.update(status="BOUNCED")
    return JsonResponse({"ok": True})

@csrf_exempt
def telegram_update(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("invalid json")

    msg = payload.get("message") or payload.get("edited_message") or {}
    return JsonResponse({"ok": True})
