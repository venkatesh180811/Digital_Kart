from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, Address


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-input", "placeholder": "Email address"}))
    phone_number = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Phone number"}))

    class Meta:
        model = User
        fields = ["username", "email", "phone_number", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-input", "placeholder": "Full name"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget = forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Password"})
        self.fields["password2"].widget = forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Confirm password"})

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = True
        user.is_email_verified = False
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-input", "placeholder": "Email address", "autofocus": True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Password"}))


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "phone_number", "profile_picture"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-input"}),
            "email": forms.EmailInput(attrs={"class": "form-input", "readonly": "readonly"}),
            "phone_number": forms.TextInput(attrs={"class": "form-input"}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ["user", "created_at"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Full name"}),
            "phone_number": forms.TextInput(attrs={"class": "form-input", "placeholder": "Phone number"}),
            "address_line1": forms.TextInput(attrs={"class": "form-input", "placeholder": "House no., building, street"}),
            "address_line2": forms.TextInput(attrs={"class": "form-input", "placeholder": "Area, landmark (optional)"}),
            "city": forms.TextInput(attrs={"class": "form-input", "placeholder": "City"}),
            "state": forms.TextInput(attrs={"class": "form-input", "placeholder": "State"}),
            "pincode": forms.TextInput(attrs={"class": "form-input", "placeholder": "Pincode"}),
            "country": forms.TextInput(attrs={"class": "form-input"}),
            "address_type": forms.Select(attrs={"class": "form-select"}),
            "is_default": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }
