from django import forms
from .models import Product, ProductImage


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ["seller", "slug", "created_at", "updated_at"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 5}),
            "mrp": forms.NumberInput(attrs={"class": "form-input"}),
            "price": forms.NumberInput(attrs={"class": "form-input"}),
            "stock": forms.NumberInput(attrs={"class": "form-input"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "subcategory": forms.Select(attrs={"class": "form-select"}),
            "brand": forms.Select(attrs={"class": "form-select"}),
        }


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["image", "alt_text", "is_primary"]
