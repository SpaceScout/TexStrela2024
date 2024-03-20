from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from multiupload.fields import MultiFileField
from mainApp.models import CustomUser, Album



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


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        default_attrs = {'onchange': 'this.form.submit()', 'style': 'color:transparent;', 'id': 'input_upload'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class MultiFileForm(forms.Form):
    files = MultipleFileField(validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'mp4', 'avi', 'mov', 'dng', 'raw'])], label=False,)


class CreateAlbum(forms.ModelForm):
    title = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'autofocus': True, 'placeholder': 'Новый альбом'})
    )

    open = forms.BooleanField(
        label='Открыть альбом',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Album
        fields = ['title', 'open']
