from rest_framework import serializers

from .models import Registro
from .services import actualizar_retiro, registrar_retiro


class RegistroSerializer(serializers.ModelSerializer):
    """Representación pública de un retiro, con resultado calculado en servidor."""

    id = serializers.IntegerField(read_only=True)
    producto = serializers.CharField(max_length=100)
    cantidad_solicitada = serializers.IntegerField(
        min_value=-(2**63),
        max_value=10000,
    )

    class Meta:
        model = Registro
        fields = (
            "id",
            "producto",
            "cantidad_solicitada",
            "resultado",
            "fecha",
        )
        read_only_fields = ("id", "resultado", "fecha")

    def validate_producto(self, valor):
        return valor.strip().casefold()

    def create(self, validated_data):
        return registrar_retiro(
            validated_data["producto"],
            validated_data["cantidad_solicitada"],
        )

    def update(self, instance, validated_data):
        # PATCH conserva el campo omitido y PUT exige ambos campos editables.
        return actualizar_retiro(
            instance,
            validated_data.get("producto", instance.producto),
            validated_data.get("cantidad_solicitada", instance.cantidad_solicitada),
        )
