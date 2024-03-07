from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from multiupload.fields import MultiFileField
from mainApp.models import Photo, CustomUser


class PasswordInputNoAutocomplete(forms.PasswordInput):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['attrs'].pop('autocomplete', None)
        return context


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(label='', required=True,
                             widget=forms.TextInput(attrs={'placeholder': 'Email'})
                             )
    password1 = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'password1', ]

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        del self.fields['password2']
        self.fields['password1'].help_text = None
        self.fields['email'].help_text = None


class CustomUserAuthForm(AuthenticationForm):
    field_order = ['email', 'password']

    email = forms.EmailField(
        label='',
        widget=forms.TextInput(attrs={'autofocus': True, 'placeholder': 'Email'})
    )
    password = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields['username']
        # Упорядочивание полей согласно заданному порядку
        self.fields = {key: self.fields[key] for key in self.field_order}


class MultiPhotoForm(forms.ModelForm):
    images = forms.FileField(validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])

    class Meta:
        model = Photo
        fields = ['images']

