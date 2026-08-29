from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

CHANNEL_CHOICES = (("email","Email"),("sms","SMS"),("telegram","Telegram"))
MODE_CHOICES = (("chain","Chain (fallback)"),("channel","Specific channel"))

class UserMultipleField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        parts = [obj.username]
        if obj.email:
            parts.append(f"📧 {obj.email}")
        phone = getattr(obj, "phone", None)
        if phone:
            parts.append(f"📱 {phone}")
        tg = getattr(obj, "telegram_username", None)
        if tg:
            parts.append(f"Telegram @{tg.lstrip('@')}")
        return " — ".join(parts)

class NotificationCreateForm(forms.Form):
    subject = forms.CharField(required=False)
    message = forms.CharField(widget=forms.Textarea, required=True)

    users = UserMultipleField(
        queryset=User.objects.all().order_by("username"),
        required=False,
        help_text="Отметьте нескольких пользователей галочками",
        widget=forms.CheckboxSelectMultiple
    )

    to_email = forms.EmailField(required=False, label="Email (ручной ввод)")
    to_phone = forms.CharField(required=False, label="Phone (ручной ввод)")
    to_telegram = forms.CharField(required=False, label="Telegram chat id (ручной ввод)")

    channels_order = forms.MultipleChoiceField(
        choices=CHANNEL_CHOICES, required=False,
        help_text="Порядок каналов (оставьте пустым для значения по умолчанию)",
        widget=forms.CheckboxSelectMultiple
    )

    mode = forms.ChoiceField(choices=MODE_CHOICES, initial="chain", required=True)
    channel = forms.ChoiceField(choices=CHANNEL_CHOICES, required=False,
                                help_text="Укажите, если выбран режим 'Specific channel'")
    idempotency_key = forms.CharField(required=False, help_text="Опционально: защита от дублей")
    send_sync = forms.BooleanField(required=False, initial=False,
                                   label="Отправить синхронно (получить результат сразу)")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("mode") == "channel" and not cleaned.get("channel"):
            self.add_error("channel", "Укажите канал в режиме 'Specific channel'.")
        if not cleaned.get("users") and not any([cleaned.get("to_email"),
                                                 cleaned.get("to_phone"),
                                                 cleaned.get("to_telegram")]):
            raise forms.ValidationError("Нужно выбрать хотя бы пользователя из базы "
                                        "или указать получателя вручную.")
        return cleaned
