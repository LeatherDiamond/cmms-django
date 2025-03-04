from buildings.models import Building

from django import forms


class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ["name", "address"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Wpisz nazwę budynku"}
            ),
            "address": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Wpisz adres budynku"}
            ),
        }
