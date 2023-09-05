from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from django_countries import Countries
from django.core.validators import RegexValidator

PAYMENT = (
    ('S', 'Tarjeta'),
    ('P', 'PayPal')
)
rfc_regex = RegexValidator(regex=r'^[A-Z&Ñ]{3,4}[0-9]{2}(0[1-9]|1[012])(0[1-9]|[12][0-9]|3[01])[A-Z0-9]{2}[0-9A]$',message= "El formato de RFC es incorrecto.",code='invalid_rfc')
phone_regex = RegexValidator(regex=r'^(\(\d{3}\)?|\d{3}?)?\d{3}?\d{4}$',message="El numero de telefono debe estar en formato 10 digitos: 'XXX XXX XXXX'.",code='invalid_phone')
zip_regex = RegexValidator(regex=r'^\d{5}$',message="El formato de codigo postal es incorrecto: 'XXXXX'.",code='invalid_zip')
class CustomCountries(Countries):
    only = ['MX']

class CheckoutForm(forms.Form):
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Calle numero, colonia, estado'
    }))
    zip = forms.CharField(validators=[zip_regex],widget=forms.TextInput(attrs={'class': 'form-control'}))
    settlement_name = forms.CharField(widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'Colonia'
    }))
    # apartment_address = forms.CharField(required=False, widget=forms.TextInput(attrs={
    #     'class': 'form-control',
    #     'placeholder': 'Direccion adicional'
    # }))
    # country = CountryField(countries=CustomCountries, blank=False, blank_label='(Seleccione pais)').formfield(widget=CountrySelectWidget(attrs={
    #     'class': 'd-block w-100'
    # }))
    country = forms.ChoiceField(widget=forms.Select(attrs={
                              'class': 'form-control wide',
                              'placeholder': 'Pais'
                          }),choices=CustomCountries)
    rfc = forms.CharField(required=False,
                          validators=[rfc_regex],
                          widget=forms.TextInput(attrs={
                              'class': 'form-control',
                              'placeholder': 'RFC'
                          }))
    phone = forms.CharField(
        validators=[phone_regex],
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'XXX XXX XXXX '
        }))
    # same_billing_address = forms.BooleanField(required=False)
    save_info = forms.BooleanField(required=False)
    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=PAYMENT)

class UserProfileForm(forms.Form):

    first_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nombre'
    }))
    last_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Apellidos'
    }))
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Calle & numero'
    }))
    apartment_address = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Direccion adicional'
    }))
    settlement_name = forms.CharField(required=False, initial="Colonia")
    rfc = forms.CharField(
        required=False,
        validators=[rfc_regex],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'RFC'
    }))
    phone = forms.CharField(
        validators=[phone_regex],
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'XXX XXX XXXX '
        }))
    # country = CountryField(countries=CustomCountries ,blank_label='(Seleccione pais)').formfield(widget=CountrySelectWidget(attrs={
    #     'class': 'd-block w-100'
    # }))
    zip = forms.CharField(validators=[zip_regex],widget=forms.TextInput(attrs={'class': 'form-control'}))
    # same_billing_address = forms.BooleanField(required=False)
    # save_info = forms.BooleanField(required=False)