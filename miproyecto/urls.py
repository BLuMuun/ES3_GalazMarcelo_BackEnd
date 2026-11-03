"""
URL configuration for miproyecto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView
from rest_framework.permissions import AllowAny
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from core.api_views import RegistroViewSet
from core.views import CerrarSesionView, IniciarSesionView

router = DefaultRouter()
router.register(r"registros", RegistroViewSet, basename="api-registro")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", IniciarSesionView.as_view(), name="login"),
    path("logout/", CerrarSesionView.as_view(), name="logout"),
    path("api/token/", TokenObtainPairView.as_view(), name="api_token"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="api_token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="api_token_verify"),
    path("api/token/blacklist/", TokenBlacklistView.as_view(), name="api_token_blacklist"),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(permission_classes=[AllowAny]),
        name="api-schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema", permission_classes=[AllowAny]),
        name="api-docs",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="api-schema", permission_classes=[AllowAny]),
        name="api-redoc",
    ),
    path("api/", include(router.urls)),
    path("registros/", include("core.urls")),
    path("", RedirectView.as_view(pattern_name="lista", permanent=False)),
]
