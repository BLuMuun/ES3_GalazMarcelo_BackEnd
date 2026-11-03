"""Regla de negocio del control de despensa.

La función se mantiene fuera de las vistas para que las operaciones web usen
una sola decisión y no dupliquen las ramas de negocio.
"""

ACEPTADO = "Aceptado: Producto retirado"


def decidir(producto, cantidad_retiro, stock_actual):
    """Devuelve uno de los cuatro resultados de la regla original.

    ``stock_actual`` es un mapeo de nombres de producto a cantidades
    disponibles, obtenido desde SQLite por la aplicación web.
    """
    producto = producto.strip().casefold()

    if cantidad_retiro <= 0:
        estado_decision = "Error: Cantidad inválida"
    elif producto not in stock_actual:
        estado_decision = "Rechazo: Producto no encontrado"
    elif cantidad_retiro > stock_actual[producto]:
        estado_decision = "Rechazo: Fuera de stock"
    elif cantidad_retiro <= stock_actual[producto]:
        estado_decision = ACEPTADO

    return estado_decision
