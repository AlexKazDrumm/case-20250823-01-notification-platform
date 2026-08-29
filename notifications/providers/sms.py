import os
from .base import SendResult, ProviderConfigError

def send_sms(message: str, to_phone: str) -> SendResult:
    provider = os.getenv("SMS_PROVIDER", "mock")
    if not to_phone:
        return SendResult(False, error="Missing recipient phone")
    if provider == "mock":
        mode = os.getenv("MOCK_SMS_MODE", "ok")
        if mode == "fail":
            return SendResult(False, error="Mock SMS failure")
        return SendResult(True, message_id="sms:mock:ok")
    elif provider == "twilio":
        try:
            from twilio.rest import Client
        except Exception as e:
            return SendResult(False, error="Twilio client not installed")
        sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        token = os.getenv("TWILIO_AUTH_TOKEN", "")
        from_number = os.getenv("TWILIO_FROM_NUMBER", "")
        if not all([sid, token, from_number]):
            raise ProviderConfigError("Twilio credentials missing")
        try:
            client = Client(sid, token)
            resp = client.messages.create(body=message, from_=from_number, to=to_phone, status_callback=os.getenv("TWILIO_STATUS_CALLBACK",""))
            return SendResult(True, message_id=resp.sid)
        except Exception as e:
            return SendResult(False, error=str(e))
    else:
        return SendResult(False, error=f"Unknown SMS provider: {provider}")
