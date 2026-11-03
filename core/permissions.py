from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from rest_framework.permissions import SAFE_METHODS, BasePermission


def tiene_rol(user, *roles):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name__in=roles).exists()
    )


def requiere_rol(*roles):
    def decorador(view_func):
        @wraps(view_func)
        @login_required(login_url="login")
        def wrapper(request, *args, **kwargs):
            if tiene_rol(request.user, *roles):
                return view_func(request, *args, **kwargs)
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("lista")

        return wrapper

    return decorador


class PermisoRegistroAPI(BasePermission):
    """Aplica a la API los mismos roles de escritura que usa la interfaz HTML."""

    message = "Tu rol no permite realizar esta operación sobre los retiros."

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True
        if request.method == "POST":
            return tiene_rol(usuario, "admin", "normal")
        if request.method in ("PUT", "PATCH", "DELETE"):
            return tiene_rol(usuario, "admin")
        return False
