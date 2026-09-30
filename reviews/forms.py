from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "title", "comment"]
        widgets = {
            "rating": forms.Select(choices=[(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)], attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-input", "placeholder": "Review title"}),
            "comment": forms.Textarea(attrs={"class": "form-input", "rows": 4, "placeholder": "Share your experience with this product"}),
        }
