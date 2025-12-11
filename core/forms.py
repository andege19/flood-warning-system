from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """
    A custom form for creating new users.
    We add 'email' and 'phone_number' to the signup.
    """
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(required=True, label="Phone Number (for SMS alerts)")

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Add 'email' and 'phone_number' to the fields
        fields = UserCreationForm.Meta.fields + ('email', 'phone_number',)