from django import forms


class RegistroForm(forms.Form):
    producto = forms.CharField(
        label="Producto",
        max_length=100,
        help_text="Escribe el nombre tal como aparece en el inventario.",
    )
    cantidad_solicitada = forms.IntegerField(
        label="Cantidad a retirar",
        min_value=-(2**63),
        max_value=10000,
    )

    def clean_producto(self):
        return self.cleaned_data["producto"].strip().casefold()