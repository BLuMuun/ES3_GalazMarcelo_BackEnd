from django.db import models
from django.utils import timezone


class Producto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["nombre"]

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip().casefold()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.stock} disponibles)"


class Registro(models.Model):
    RESULTADO_CHOICES = (
        ("Error: Cantidad inválida", "Error: Cantidad inválida"),
        ("Rechazo: Producto no encontrado", "Rechazo: Producto no encontrado"),
        ("Rechazo: Fuera de stock", "Rechazo: Fuera de stock"),
        ("Aceptado: Producto retirado", "Aceptado: Producto retirado"),
    )

    producto = models.CharField(max_length=100)
    cantidad_solicitada = models.IntegerField()
    resultado = models.CharField(max_length=100, choices=RESULTADO_CHOICES)
    fecha = models.DateTimeField(default=timezone.now)
    afecta_stock = models.BooleanField(default=False)
    eliminado = models.BooleanField(default=False)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha", "-pk"]
        verbose_name = "registro de retiro"
        verbose_name_plural = "registros de retiros"

    def __str__(self):
        return f"{self.producto} - {self.resultado}"

    def soft_delete(self):
        self.eliminado = True
        self.fecha_eliminacion = timezone.now()
        self.save(update_fields=["eliminado", "fecha_eliminacion"])
