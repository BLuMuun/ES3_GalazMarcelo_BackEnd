import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Registro


class Command(BaseCommand):
    help = "Importa una sola vez el historial legado de datos.json a SQLite."

    def handle(self, *args, **options):
        ruta = settings.BASE_DIR / "datos.json"
        if not ruta.exists():
            raise CommandError(f"No se encontró el archivo legado: {ruta}")
        if Registro.objects.exists():
            raise CommandError(
                "Ya hay registros en SQLite. La importación se detuvo para no duplicar el historial."
            )

        try:
            with ruta.open("r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except (OSError, json.JSONDecodeError) as error:
            raise CommandError(f"No se pudo leer datos.json: {error}") from error

        if not isinstance(datos, list):
            raise CommandError("datos.json debe contener una lista de registros.")

        registros = []
        resultados_validos = {valor for valor, _ in Registro.RESULTADO_CHOICES}
        for indice, item in enumerate(datos, start=1):
            if not isinstance(item, dict):
                raise CommandError(f"El registro {indice} no es un objeto JSON.")
            try:
                producto = item["producto"]
                cantidad = int(item["cantidad_solicitada"])
                resultado = item["resultado"]
            except (KeyError, TypeError, ValueError) as error:
                raise CommandError(f"El registro {indice} no tiene el formato esperado.") from error
            if not isinstance(producto, str) or not producto.strip():
                raise CommandError(f"El producto del registro {indice} está vacío o no es texto.")
            if not isinstance(resultado, str) or resultado not in resultados_validos:
                raise CommandError(f"El resultado del registro {indice} no coincide con la regla actual.")
            producto = producto.strip().casefold()
            registros.append(
                Registro(
                    producto=producto,
                    cantidad_solicitada=cantidad,
                    resultado=resultado,
                )
            )

        with transaction.atomic():
            Registro.objects.bulk_create(registros)
        self.stdout.write(self.style.SUCCESS(f"Se importaron {len(registros)} registros desde datos.json."))
        self.stdout.write("La importación preservó el historial y no alteró el stock inicial del inventario.")
