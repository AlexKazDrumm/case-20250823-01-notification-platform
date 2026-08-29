from django.core.mail import EmailMessage, get_connection
from django.conf import settings
from .base import SendResult, ProviderConfigError
import boto3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Dict
import re

def _normalize_attachments(attachments: List[Dict]) -> List[Dict]:
    return attachments or []

def send_email(subject: str, message: str, to_email: str, attachments: List[Dict] | None = None) -> SendResult:
    if not to_email:
        return SendResult(False, error="Missing recipient email")
    provider = getattr(settings, "EMAIL_PROVIDER", "django")
    if provider == "ses":
        return _send_via_ses(subject or "(no subject)", message, to_email, _normalize_attachments(attachments))
    else:
        return _send_via_django(subject or "(no subject)", message, to_email, _normalize_attachments(attachments))

def _send_via_django(subject: str, message: str, to_email: str, attachments: List[Dict]) -> SendResult:
    try:
        email = EmailMessage(subject=subject, body=message, from_email=settings.DEFAULT_FROM_EMAIL, to=[to_email])
        for att in attachments:
            if "content" in att and "filename" in att:
                email.attach(att["filename"], att["content"], att.get("content_type","application/octet-stream"))
        email.send(fail_silently=False)
        return SendResult(True, message_id="email:django:ok")
    except Exception as e:
        return SendResult(False, error=str(e))

def _send_via_ses(subject: str, message: str, to_email: str, attachments: List[Dict]) -> SendResult:
    ses = boto3.client("ses", region_name=getattr(settings, "AWS_REGION","eu-central-1"))
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = getattr(settings, "AWS_SES_SENDER", settings.DEFAULT_FROM_EMAIL)
    msg["To"] = to_email
    msg.attach(MIMEText(message, "plain", "utf-8"))
    s3_attachments = [a for a in attachments if a.get("s3_uri")]
    direct_attachments = [a for a in attachments if a.get("content")]

    s3 = boto3.client("s3", region_name=getattr(settings,"AWS_REGION","eu-central-1"))
    for att in s3_attachments:
        uri = att["s3_uri"]
        m = re.match(r"^s3://([^/]+)/(.+)$", uri)
        if not m:
            continue
        bucket, key = m.group(1), m.group(2)
        obj = s3.get_object(Bucket=bucket, Key=key)
        data = obj["Body"].read()
        part = MIMEApplication(data)
        part.add_header("Content-Disposition", "attachment", filename=att.get("filename", key.split("/")[-1]))
        msg.attach(part)

    for att in direct_attachments:
        part = MIMEApplication(att["content"])
        part.add_header("Content-Disposition", "attachment", filename=att.get("filename","file.bin"))
        msg.attach(part)

    try:
        resp = ses.send_raw_email(RawMessage={"Data": msg.as_string()})
        message_id = resp.get("MessageId","ses:ok")
        return SendResult(True, message_id=message_id)
    except Exception as e:
        return SendResult(False, error=str(e))
