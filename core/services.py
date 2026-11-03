from django.db import transaction

from solucion import ACEPTADO, decidir

from .models import Producto, Registro


def _productos_bloqueados():
    return list(Producto.objects.select_for_update().all())


def registrar_retiro(nombre, cantidad):
    nombre = nombre.strip().casefold()

    with transaction.atomic():
        productos = _productos_bloqueados()
        stock_actual = {producto.nombre: producto.stock for producto in productos}
        resultado = decidir(nombre, cantidad, stock_actual)

        if resultado == ACEPTADO:
            producto = next(item for item in productos if item.nombre == nombre)
            producto.stock -= cantidad
            producto.save(update_fields=["stock"])

        return Registro.objects.create(
            producto=nombre,
            cantidad_solicitada=cantidad,
            resultado=resultado,
            afecta_stock=(resultado == ACEPTADO),
        )


def actualizar_retiro(registro, nombre, cantidad):
    nombre = nombre.strip().casefold()

    with transaction.atomic():
        registro = Registro.objects.select_for_update().get(pk=registro.pk, eliminado=False)
        productos = _productos_bloqueados()

        if registro.afecta_stock:
            anterior = next((item for item in productos if item.nombre == registro.producto), None)
            if anterior is not None:
                anterior.stock += registro.cantidad_solicitada
                anterior.save(update_fields=["stock"])

        stock_actual = {producto.nombre: producto.stock for producto in productos}
        resultado = decidir(nombre, cantidad, stock_actual)

        if resultado == ACEPTADO:
            nuevo = next(item for item in productos if item.nombre == nombre)
            nuevo.stock -= cantidad
            nuevo.save(update_fields=["stock"])

        registro.producto = nombre
        registro.cantidad_solicitada = cantidad
        registro.resultado = resultado
        registro.afecta_stock = resultado == ACEPTADO
        registro.save(
            update_fields=["producto", "cantidad_solicitada", "resultado", "afecta_stock"]
        )
        return registro


def eliminar_retiro(registro):
    with transaction.atomic():
        registro = Registro.objects.select_for_update().get(pk=registro.pk, eliminado=False)
        if registro.afecta_stock:
            productos = _productos_bloqueados()
            producto = next((item for item in productos if item.nombre == registro.producto), None)
            if producto is not None:
                producto.stock += registro.cantidad_solicitada
                producto.save(update_fields=["stock"])
        registro.soft_delete()
        return registro
