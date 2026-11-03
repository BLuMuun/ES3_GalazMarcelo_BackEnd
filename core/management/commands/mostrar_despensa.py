from django.core.management.base import BaseCommand
from tabulate import tabulate

from core.models import Producto


class Command(BaseCommand):
    help = "Muestra el inventario actual de SQLite en una tabla de consola."

    def handle(self, *args, **options):
        filas = list(Producto.objects.values_list("nombre", "stock"))
        if not filas:
            self.stdout.write("No hay productos en el inventario.")
            return
        self.stdout.write(tabulate(filas, headers=("Producto", "Stock disponible"), tablefmt="grid"))
