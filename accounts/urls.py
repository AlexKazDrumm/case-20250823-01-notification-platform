from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, AuthTokenView

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("token/", AuthTokenView.as_view(), name="token"),
    path("", include(router.urls)),
]
