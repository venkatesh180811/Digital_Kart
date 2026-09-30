from django import forms
from .models import SellerProfile


class SellerRegistrationForm(forms.ModelForm):
    class Meta:
        model = SellerProfile
        fields = ["business_name", "gstin", "business_address"]
        widgets = {
            "business_name": forms.TextInput(attrs={"class": "form-input"}),
            "gstin": forms.TextInput(attrs={"class": "form-input", "placeholder": "Optional"}),
            "business_address": forms.Textarea(attrs={"class": "form-input", "rows": 3}),
        }
