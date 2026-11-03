from rest_framework import viewsets

from .models import Registro
from .permissions import PermisoRegistroAPI
from .serializers import RegistroSerializer
from .services import eliminar_retiro


class RegistroViewSet(viewsets.ModelViewSet):
    """CRUD REST de retiros, manteniendo la lógica de inventario compartida."""

    serializer_class = RegistroSerializer
    permission_classes = (PermisoRegistroAPI,)

    def get_queryset(self):
        # No exponer los registros que se ocultaron mediante borrado lógico.
        return Registro.objects.filter(eliminado=False)

    def perform_destroy(self, instance):
        # ModelViewSet responderá 204; el servicio restaura stock y conserva el registro.
        eliminar_retiro(instance)
