from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RegistroForm
from .models import Producto, Registro
from .permissions import requiere_rol, tiene_rol
from .services import actualizar_retiro, eliminar_retiro, registrar_retiro


class IniciarSesionView(LoginView):
    template_name = "registration/login.html"


class CerrarSesionView(LogoutView):
    next_page = "login"


@login_required(login_url="login")
def lista(request):
    contexto = {
        "registros": Registro.objects.filter(eliminado=False),
        "productos": Producto.objects.all(),
        "puede_crear": tiene_rol(request.user, "admin", "normal"),
        "puede_administrar": tiene_rol(request.user, "admin"),
    }
    return render(request, "resumen.html", contexto)


@requiere_rol("admin", "normal")
def crear(request):
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        registro = registrar_retiro(
            form.cleaned_data["producto"],
            form.cleaned_data["cantidad_solicitada"],
        )
        if registro.resultado.startswith("Aceptado:"):
            messages.success(request, registro.resultado)
        else:
            messages.warning(request, registro.resultado)
        return redirect("lista")
    return render(request, "form.html", {"form": form, "accion": "Registrar retiro"})


@requiere_rol("admin")
def editar(request, pk):
    registro = get_object_or_404(Registro, pk=pk, eliminado=False)
    inicial = {
        "producto": registro.producto,
        "cantidad_solicitada": registro.cantidad_solicitada,
    }
    form = RegistroForm(request.POST or None, initial=inicial)
    if request.method == "POST" and form.is_valid():
        registro = actualizar_retiro(
            registro,
            form.cleaned_data["producto"],
            form.cleaned_data["cantidad_solicitada"],
        )
        messages.success(request, f"Registro actualizado: {registro.resultado}")
        return redirect("lista")
    return render(
        request,
        "form.html",
        {"form": form, "accion": "Editar retiro", "registro": registro},
    )


@requiere_rol("admin")
def eliminar(request, pk):
    registro = get_object_or_404(Registro, pk=pk, eliminado=False)
    if request.method == "POST":
        eliminar_retiro(registro)
        messages.success(request, "El registro se ocultó del historial y el stock se restauró si correspondía.")
        return redirect("lista")
    return render(request, "confirmar.html", {"registro": registro})
