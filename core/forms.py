# core/forms.py
from django import forms
from django.core.validators import EmailValidator, RegexValidator

class MongoLoginForm(forms.Form):
    username = forms.CharField(label='Usuario de MongoDB', max_length=100)
    password = forms.CharField(label='Contraseña de MongoDB', widget=forms.PasswordInput)

class ClienteForm(forms.Form):
    nombre = forms.CharField(
        max_length=100,
        label='Nombre',
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': 'true'})
    )
    email = forms.EmailField(
        label='Email',
        validators=[EmailValidator(message="Ingrese un email válido.")],
        widget=forms.EmailInput(attrs={'class': 'form-control', 'required': 'true'})
    )
    fecha_registro = forms.DateField(
        label='Fecha de registro',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': 'true'})
    )
    direccion = forms.CharField(
        max_length=200,
        label='Dirección',
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': 'true'})
    )
    telefono = forms.CharField(
        max_length=15,
        label='Teléfono',
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Formato de teléfono inválido.")],
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': 'true'})
    )




class PedidoForm(forms.Form):
    cliente = forms.ChoiceField(
        choices=[],
        label='Cliente',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'min-width: 300px;''min-height: 50px',  
            'required': 'true'
        })
    )
    fecha_pedido = forms.DateField(
        label='Fecha del pedido',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': 'true'})
    )
    productos = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        label='Productos'
    )

    def __init__(self, *args, **kwargs):
        clientes = kwargs.pop('clientes', [])
        productos = kwargs.pop('productos', [])
        super(PedidoForm, self).__init__(*args, **kwargs)
        self.fields['cliente'].choices = [('', 'Seleccione un cliente')] + [(c['_id'], c['nombre']) for c in clientes]
        self.fields['productos'].choices = [(p['id_producto'], f"{p['nombre']} - ${p['precio']}") for p in productos]

    def clean(self):
        cleaned_data = super().clean()
        productos = cleaned_data.get('productos')
        if not productos:
            raise forms.ValidationError("Debe seleccionar al menos un producto.")
        return cleaned_data




class ProductoForm(forms.Form):
    id_producto = forms.CharField(
        max_length=100,
        label='ID del producto',
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': 'true'})
    )
    nombre = forms.CharField(
        max_length=100,
        label='Nombre del producto',
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': 'true'})
    )
    precio = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label='Precio',
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'required': 'true', 'step': '0.01'})
    )

    def clean_id_producto(self):
        id_producto = self.cleaned_data['id_producto']
        return id_producto

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        return nombre