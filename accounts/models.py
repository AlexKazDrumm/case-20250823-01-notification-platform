from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone = models.CharField(max_length=32, blank=True, null=True)
    telegram_username = models.CharField(max_length=64, blank=True, null=True)
    telegram_chat_id = models.CharField(max_length=32, blank=True, null=True)

    def __str__(self):
        return self.username
