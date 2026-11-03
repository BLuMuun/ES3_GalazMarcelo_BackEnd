from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea los grupos de acceso admin, normal y viewer."

    def handle(self, *args, **options):
        for nombre in ("admin", "normal", "viewer"):
            _, creado = Group.objects.get_or_create(name=nombre)
            estado = "creado" if creado else "ya existía"
            self.stdout.write(f"Grupo {nombre}: {estado}.")
