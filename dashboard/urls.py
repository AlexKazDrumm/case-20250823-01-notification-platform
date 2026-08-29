from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("notifications/", views.notifications_list, name="notifications_list"),
    path("notifications/create/", views.notification_create, name="notification_create"),
    path("notifications/<int:pk>/", views.notification_detail, name="notification_detail"),
    path("notifications/<int:pk>/resend/", views.notification_resend, name="notification_resend"),
    path("users/", views.users_list, name="users_list"),
]
