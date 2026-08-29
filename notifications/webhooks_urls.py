from django.urls import path
from .webhooks_views import ses_sns, twilio_sms, telegram_update

urlpatterns = [
    path("ses/", ses_sns, name="ses_sns"),
    path("twilio/", twilio_sms, name="twilio_sms"),
    path("telegram/", telegram_update, name="telegram_update"),
]
