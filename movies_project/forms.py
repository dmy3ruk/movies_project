from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

class RegistrationForm(UserCreationForm):
    username = forms.CharField(
        label=_(""),
        max_length=30,
        help_text=None,
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': "input"}),
    )
    email = forms.EmailField(
        label="",
        widget=forms.EmailInput(attrs={'placeholder': 'Email', 'class': "input"})
    )
    password1 = forms.CharField(
        label="",
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': "input"}),
        help_text=None,
    )
    password2 = forms.CharField(
        label="",
        widget=forms.PasswordInput(attrs={'placeholder': 'Password confirmation', 'class': "input"}),
        help_text=None,
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label=_(""),
        max_length=30,
        help_text=None,
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': "input"}),
    )
    password = forms.CharField(
        label="",
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': "input"}),
        help_text=None,
    )
    class Meta:
        fields = ['username', 'password']
