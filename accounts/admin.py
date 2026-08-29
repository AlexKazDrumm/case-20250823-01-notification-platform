from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Contacts", {"fields": ("phone", "telegram_username", "telegram_chat_id")}),
    )
    list_display = ("username","email","is_staff","phone","telegram_username", "telegram_chat_id")
    search_fields = ("username","email","phone","telegram_username")
