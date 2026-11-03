from django.contrib import admin
from .models import Producto, Registro

admin.site.site_header = "Administración de Despensa Familiar"
admin.site.site_title = "Despensa Familiar"
admin.site.index_title = "Inventario e historial"


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "stock")
    search_fields = ("nombre",)
    ordering = ("nombre",)

    def get_readonly_fields(self, request, obj=None):
        return ("nombre",) if obj else ()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    list_display = ("producto", "cantidad_solicitada", "resultado", "fecha", "eliminado")
    list_filter = ("resultado", "eliminado")
    search_fields = ("producto",)
    date_hierarchy = "fecha"
    readonly_fields = (
        "producto",
        "cantidad_solicitada",
        "resultado",
        "fecha",
        "afecta_stock",
        "eliminado",
        "fecha_eliminacion",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
