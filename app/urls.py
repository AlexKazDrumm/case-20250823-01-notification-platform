from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from strawberry.django.views import GraphQLView
from .schema import schema


urlpatterns = [
    path("", include("dashboard.urls")),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/notifications/", include("notifications.urls")),
    path("graphql", GraphQLView.as_view(schema=schema)),
]

urlpatterns += [
    path("api/auth/", include("accounts.urls")),
]

urlpatterns += [
    path("webhooks/", include("notifications.webhooks_urls")),
]
