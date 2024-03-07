from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import render, redirect

from mainApp.forms import CustomUserCreationForm, MultiPhotoForm, CustomUserAuthForm
from mainApp.models import Photo


def home_view(request):
    register_form = CustomUserCreationForm()
    login_form = CustomUserAuthForm()
    show_registration_form = False
    show_login_form = False
    if request.method == 'POST':
        print("GOT POST AUTH")
        print(request.POST)
        if 'register_form' in request.POST:
            register_form = CustomUserCreationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                login(request, user)
                return redirect('user_gallery')  # Укажите свое представление для переадресации после регистрации
            else:
                show_registration_form = True

        elif 'login_form' in request.POST:
            login_form = CustomUserAuthForm(request, request.POST)
            if login_form.is_valid():
                # user = login_form.get_user()
                user = authenticate(request, email=login_form.cleaned_data['email'],
                                    password=login_form.cleaned_data['password'])
                if user is not None:
                    # Пользователь успешно аутентифицирован
                    login(request, user)
                    return redirect('user_gallery')  # Укажите свое представление для переадресации после входа
                else:
                    # Аутентификация не удалась
                    show_login_form = True
            else:
                show_login_form = True

    return render(request, 'Home.html', {'registration_form': register_form, 'login_form': login_form,
                                         'show_registration_form': show_registration_form,
                                         'show_login_form': show_login_form})


@login_required
def gallery_view(request):
    photos = Photo.objects.filter(user=request.user)
    return render(request, 'photo_list.html', {'photos': photos})


@login_required
def gallery_view(request):
    try:
        if request.method == 'POST':
            print(request.POST)
            form = MultiPhotoForm(request.POST, request.FILES)
            if form.is_valid():
                for image in request.FILES.getlist('images'):
                    Photo.objects.create(user=request.user, image=image)
            return redirect('user_gallery')
        else:
            form = MultiPhotoForm()
            photos = Photo.objects.filter(user=request.user)
            return render(request, 'Gallery.html', {'photos': photos, 'form': form})
    except ValueError:
        return redirect('user_gallery')
    

@login_required
def change_image_view(request):
    if request.method == 'GET':
        photo_url = request.GET.get('photo')
        if photo_url:
            return render(request, 'ChangeImage.html', {'photourl': photo_url})

