from datetime import datetime
import json
import os
from io import BytesIO
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import Http404, JsonResponse, FileResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.images import get_image_dimensions
from PIL import Image, ImageEnhance, ImageDraw, ImageFont, ExifTags
import io
import zipfile
import numpy as np

from django.views.decorators.csrf import csrf_exempt

from mainApp.forms import CustomUserCreationForm, MultiFileForm, CustomUserAuthForm, CreateAlbum
from mainApp.models import Files, Album, CustomUser, Tag


def home_view(request):
    register_form = CustomUserCreationForm()
    login_form = CustomUserAuthForm()
    show_registration_form = False
    show_login_form = False
    if request.method == 'POST':
        print(request.POST)
        if 'register_form' in request.POST:
            register_form = CustomUserCreationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                login(request, user)
                return redirect('gallery')
            else:
                show_registration_form = True

        elif 'login_form' in request.POST:
            login_form = CustomUserAuthForm(request, request.POST)
            if login_form.is_valid():
                user = authenticate(request, email=login_form.cleaned_data['email'],
                                    password=login_form.cleaned_data['password'])
                if user is not None:
                    login(request, user)
                    return redirect('gallery')
                else:
                    show_login_form = True
            else:
                show_login_form = True

    return render(request, 'Home.html', {'registration_form': register_form, 'login_form': login_form,
                                         'show_registration_form': show_registration_form,
                                         'show_login_form': show_login_form})


def is_image(file):
    try:
        # Пытаемся получить размеры изображения
        width, height = get_image_dimensions(file)
        if not width or not height:
            # Если не получается, это не изображение
            return False
        return True
    except:
        # В случае ошибки тоже считаем, что это не изображение
        return False


from ultralytics import YOLO
modelYolo = YOLO("yolov8x.pt")
from deepface import DeepFace


def get_decimal_from_dms(dms, ref):
    degrees, minutes, seconds = dms
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

def get_image_metadata(file_path):
    image = Image.open(file_path)
    metadata = {
        "file_size": image.size,  # Размер изображения в пикселях
        "author": None,  # Автор будет заполнен, если присутствует в EXIF
        "date_taken": None,  # Дата съёмки
        "location": None,  # Геолокация
    }

    # Получение метаданных EXIF
    exif_data = image._getexif()
    if exif_data:
        for tag_id, value in exif_data.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            if tag == "Artist":
                metadata['author'] = value
            elif tag == "DateTimeOriginal":
                try:
                    metadata['date_taken'] = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                except ValueError:
                    pass  # Неверный формат даты
            elif tag == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_tag = ExifTags.GPSTAGS.get(t, t)
                    gps_data[sub_tag] = value[t]

                if 'GPSLatitude' in gps_data and 'GPSLongitude' in gps_data:
                    lat = get_decimal_from_dms(gps_data['GPSLatitude'], gps_data['GPSLatitudeRef'])
                    lon = get_decimal_from_dms(gps_data['GPSLongitude'], gps_data['GPSLongitudeRef'])
                    metadata['location'] = (lat, lon)

    return metadata



@login_required
def gallery_view(request):
    try:
        if request.method == 'POST':
            form = MultiFileForm(request.POST, request.FILES)
            if form.is_valid():

                for file in request.FILES.getlist('files'):
                    file_name = "ebaka"
                    try:
                        file_name = file.file.name.lower()
                    except:
                        pass

                    if (is_image(file) and not file_name.endswith(".dng")):
                        image = Image.open(file)
                        results = modelYolo.predict(image)
                        result = results[0]
                        tags = []
                        for box in result.boxes:
                            class_id = result.names[box.cls[0].item()]
                            tags.append(class_id)
                            print(class_id)
                        title = file.name
                        metadata = get_image_metadata(file)

                        detected_face = False

                        try:
                            cv_image = np.array(image)
                            cv_image = cv_image[:, :, ::-1].copy()  # PIL использует RGB, OpenCV использует BGR
                            if len(DeepFace.extract_faces(img_path=cv_image, align=True)) > 0:
                                detected_face = True  # Установка поля face_detected в True, если лицо обнаружено
                            # image.close()
                            # np.allclose()
                        except Exception:
                            pass

                        new_file = Files.objects.create(user=request.user, file=file, title=title, 
                                                        author=metadata.get('author'),
                                                        date_taken=metadata.get('date_taken'),
                                                        location=metadata.get('location'),
                                                        face_detected=detected_face)
                        for tag in tags:
                            if not new_file.tags.filter(name=tag).exists():
                                new_tag, created = Tag.objects.get_or_create(name=tag)
                                new_file.tags.add(new_tag)
                        new_file.save()
                    else:
                        new_file = Files.objects.create(user=request.user, file=file, title=file.name)
                        new_file.save()
            return redirect('gallery')
        else:
            form = MultiFileForm()
            search_query = request.GET.get('search', '')
            query = Q(user=request.user) & (
                Q(file__endswith='.jpg') | Q(file__endswith='.jpeg') |
                Q(file__endswith='.png') | Q(file__endswith='.raw') | Q(file__endswith='.dng')
            )
            if ':' in search_query:
                filter_type, filter_value = search_query.split(':', 1)

                # Примеры фильтров
                if filter_type == 'Дата создания':
                    filter_value = filter_value.strip()
                    # Проверка, является ли filter_value просто годом (четырехзначным числом)
                    if len(filter_value) == 4 and filter_value.isdigit():
                        try:
                            year_value = int(filter_value)
                            # Создаем фильтр для изображений, сделанных в любое время в указанный год
                            query &= Q(date_taken__year=year_value)
                        except ValueError:
                            pass  # В случае, если значение не является действительным годом
                    else:
                        try:
                            # Преобразование строки в объект datetime
                            date_value = datetime.strptime(filter_value, '%Y-%m-%d')
                            query &= Q(date_taken=date_value)
                        except ValueError:
                            pass  # Неверный формат даты
                elif filter_type == 'Автор':
                    query &= Q(author__icontains=filter_value.strip())
                elif filter_type == 'Геолокация':
                    query &= Q(location__icontains=filter_value.strip())
                elif filter_type == 'Тег':
                    query &= Q(tags__name__icontains=filter_value)
                elif filter_type == 'Совпадения':
                    reference_image_path = "." + filter_value  # Эталонное изображение
                    db_path = os.path.dirname(reference_image_path)  # Папка для поиска
                    
                    try:   # Выполняем поиск совпадений с эталонным изображением
                        results = DeepFace.find(img_path=reference_image_path, db_path=db_path)
                        similar_images = [item for result in results if 'identity' in result for item in result['identity']]
                        similar_images_names = [os.path.basename(path) for path in similar_images]
                        queries = [Q(file__icontains=image_name) for image_name in similar_images_names]

                        # Объединяем все условия в одно с помощью оператора OR
                        combined_query = queries.pop()

                        for individual_query in queries:
                            combined_query |= individual_query

                        # Добавляем combined_query к основному запросу
                        query &= combined_query
                    except Exception as e:
                        print(f"Произошла ошибка при выполнении DeepFace.find: {e}")
                # Добавьте другие условия фильтрации

                photos = Files.objects.filter(query)
            else:
                photos = Files.objects.filter(query)

            return render(request, 'Gallery.html', {'photos': photos, 'form': form, 'search_query': search_query})
    except ValueError as e:
        print(e)
        return redirect('gallery')


def resize_and_crop(image, target_width, target_height, crop_mode='top'):
    """
    Масштабирует и обрезает изображение до заданных размеров, сохраняя пропорции.
    crop_mode может быть 'top', 'middle' или 'bottom'.
    """
    pil_image = Image.open(image)

    # Исходные размеры и соотношение сторон изображения
    orig_width, orig_height = pil_image.size
    orig_ratio = orig_width / orig_height

    # Целевое соотношение сторон
    target_ratio = target_width / target_height

    # Масштабирование изображения
    if orig_ratio > target_ratio:
        # Изображение слишком широкое, масштабируем по высоте
        scale_height = target_height
        scale_width = int(scale_height * orig_ratio)
    else:
        # Изображение слишком высокое, масштабируем по ширине
        scale_width = target_width
        scale_height = int(scale_width / orig_ratio)

    scaled_image = pil_image.resize((scale_width, scale_height), Image.Resampling.LANCZOS)

    # Расчет начальных координат для обрезки
    if crop_mode == 'top':
        x0 = (scale_width - target_width) // 2
        y0 = 0
    elif crop_mode == 'middle':
        x0 = (scale_width - target_width) // 2
        y0 = (scale_height - target_height) // 2
    else: # bottom
        x0 = (scale_width - target_width) // 2
        y0 = scale_height - target_height

    # Обрезка изображения
    cropped_image = scaled_image.crop((x0, y0, x0 + target_width, y0 + target_height))

    return cropped_image


def show_image(request, file_id):
    try:
        file = Files.objects.get(id=file_id)
        image_data = io.BytesIO(file.file.read())
        image = resize_and_crop(image_data, 300, 300)


        jpeg_data = io.BytesIO()
        image.save(jpeg_data, format='png')
        image.close()

        value = jpeg_data.getvalue()
        jpeg_data.close()
        image_data.close()
        file.file.close()

        # Возвращаем JPEG изображение в HttpResponse
        return HttpResponse(value, content_type='image/png')
    except Files.DoesNotExist:
        return HttpResponse(status=404, content="File not found")
    
    
def show_image_orig(request, file_id):
    try:
        file = Files.objects.get(id=file_id)
        image_data = io.BytesIO(file.file.read())
        image = Image.open(image_data)

        jpeg_data = io.BytesIO()
        image.save(jpeg_data, format='png')
        image.close()

        value = jpeg_data.getvalue()
        jpeg_data.close()
        image_data.close()
        file.file.close()
        # Возвращаем JPEG изображение в HttpResponse
        return HttpResponse(value, content_type='image/png')
    except Files.DoesNotExist:
        return HttpResponse(status=404, content="File not found")


@login_required
def albums_view(request):
    try:
        if request.method == 'POST':
            album_form = CreateAlbum(request.POST)
            if album_form.is_valid():
                album = Album.objects.create(user=request.user, title=album_form.cleaned_data['title'], open=album_form.cleaned_data['open'])
                return redirect('photo_add', album_id=album.id)
        else:
            form = MultiFileForm()
            album_form = CreateAlbum()
            shared_albums = Album.objects.filter(allowed_users__id=request.user.id)
            albums = Album.objects.filter(user_id=request.user.id)
            return render(request, 'Albums.html',
                          {'shared_albums': shared_albums, 'albums': albums, 'form': form, 'album_form': album_form})
    except ValueError:
        return redirect('albums')


def album_view(request, album_id):
    all_user_emails = CustomUser.objects.values_list('email', flat=True)
    user = request.user

    album = get_object_or_404(Album, pk=album_id)
    allowed_users = album.allowed_users.all()

    photos = Files.objects.filter(
        Q(file__endswith='.jpg', albums_files__id=album_id) |
        Q(file__endswith='.jpeg', albums_files__id=album_id) |
        Q(file__endswith='.png', albums_files__id=album_id) |
        Q(file__endswith='.raw', albums_files__id=album_id) |
        Q(file__endswith='.dng', albums_files__id=album_id)
    )
    videos = Files.objects.filter(
        Q(file__endswith='.mp4', albums_files__id=album_id) |
        Q(file__endswith='.avi', albums_files__id=album_id) |
        Q(file__endswith='.mov', albums_files__id=album_id)
    )
    if album.open:
        return render(request, 'SomeAlbum.html',
                      {'member': True, 'user': user, 'album': album, 'photos': photos, 'videos': videos})
    elif request.user == album.user:
        if allowed_users:
            return render(request, 'SomeAlbum.html',
                          {'allowed_users': allowed_users, 'user': user, 'album': album, 'photos': photos,
                           'videos': videos,
                           'emails': all_user_emails})
        else:
            return render(request, 'SomeAlbum.html',
                          {'allowed_users': False, 'user': user, 'album': album, 'photos': photos, 'videos': videos,
                           'emails': all_user_emails})
    elif request.user in allowed_users:
        return render(request, 'SomeAlbum.html',
                      {'member': True, 'user': user, 'album': album, 'photos': photos, 'videos': videos})
    else:
        raise Http404("File not found")


@login_required
def add_files_to_album(request, album_id):
    try:
        album = get_object_or_404(Album, id=album_id)
        if request.method == 'POST':
            selected_photos_ids = request.POST.getlist('selected_photos')
            selected_videos_ids = request.POST.getlist('selected_videos')
            for video_id in selected_videos_ids:
                video = get_object_or_404(Files, id=video_id, user=request.user)
                new_video = album.files.add(video)
            for photo_id in selected_photos_ids:
                photo = get_object_or_404(Files, id=photo_id, user=request.user)
                album.files.add(photo)
            return redirect('album_files', album_id=album.id)
        else:
            photos = Files.objects.filter(
                Q(user=request.user, file__endswith='.jpg') |
                Q(user=request.user, file__endswith='.jpeg') |
                Q(user=request.user, file__endswith='.png') |
                Q(user=request.user, file__endswith='.raw') |
                Q(user=request.user, file__endswith='.dng')
            )
            videos = Files.objects.filter(
                Q(user=request.user, file__endswith='.mp4') |
                Q(user=request.user, file__endswith='.avi') |
                Q(user=request.user, file__endswith='.mov')
            )
            return render(request, 'ChooseFilesToAdd.html', {'photos': photos, 'videos': videos})
    except Exception as e:
        return redirect('albums')


@login_required
def videos_view(request):
    try:
        if request.method == 'POST':
            form = MultiFileForm(request.POST, request.FILES)
            if form.is_valid():
                for file in request.FILES.getlist('files'):
                    Files.objects.create(user=request.user, file=file)
            return redirect('videos')
        else:
            form = MultiFileForm()
            videos = Files.objects.filter(
                Q(user=request.user, file__endswith='.mp4') |
                Q(user=request.user, file__endswith='.avi') |
                Q(user=request.user, file__endswith='.mov')
            )
            return render(request, 'Videos.html', {'videos': videos, 'form': form})
    except ValueError:
        return redirect('videos')


@login_required
def delete_file(request, file_id):
    file_to_delete = get_object_or_404(Files, id=file_id, user=request.user)
    # Проверка, принадлежит ли файл пользователю для безопасности
    if file_to_delete.user != request.user:
        raise Http404("File not found")

    try:
        file_to_delete.file.delete()
        return JsonResponse({'message': 'File successfully deleted'})
    except Exception as e:
        print(f"Error deleting file: {e}")
        return JsonResponse({'error': 'Failed to delete file'}, status=500)


@login_required
# @csrf_exempt
def delete_file_from_album(request, album_id, file_id):
    album = get_object_or_404(Album, pk=album_id)
    file_to_delete = get_object_or_404(Files, id=file_id)
    # Проверка, принадлежит ли файл пользователю для безопасности
    # if file_to_delete.user != request.user:
    #     raise Http404("File not found")
    print("Ebaka")
    try:
        if file_to_delete in album.files.all():
            print("Ebaka")
            album.files.remove(file_to_delete)
            # Теперь сохраните изменения
            album.save()
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            else:
                return redirect('albums')
        else:
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            else:
                return redirect('albums')
    except Exception as e:
        print(f"Error deleting file: {e}")
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        else:
            return redirect('albums')


@login_required
def download_file_view(request, file_id):
    file_object = get_object_or_404(Files, id=file_id)
    response = FileResponse(open(file_object.file.path, 'rb'))

    # Устанавливаем заголовки для скачивания файла
    response['Content-Disposition'] = f'attachment; filename="{file_object.file.name}"'
    return response


@login_required
def download_album(request, album_id):
    # Получаем альбом по его ID
    album = Album.objects.get(id=album_id)

    # Создаем объект для записи в память
    zip_buffer = io.BytesIO()

    # Создаем zip-архив в памяти
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zipf:
        # Добавляем файлы альбома в zip-архив
        for file in album.files.all():
            file_content = file.file.read()  # Читаем содержимое файла
            file_name = os.path.basename(file.file.name)
            zipf.writestr(file_name, file_content)

    # Устанавливаем указатель в начало объекта для чтения из памяти
    zip_buffer.seek(0)

    # Отправляем zip-архив как ответ
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{album.title}.zip"'
    file.file.close()
    zip_buffer.close()
    return response


@login_required
def add_user_to_album(request):
    user_email = request.GET.get('user_email')
    album_id = request.GET.get('album_id')

    album = get_object_or_404(Album, pk=album_id)
    if request.user == album.user:
        user_to_add = get_object_or_404(CustomUser, email=user_email)
        album.allowed_users.add(user_to_add)
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        else:
            return redirect('albums')
    else:
        raise Http404("Auth error")


@login_required
def delete_user_from_album(request):
    user_email = request.GET.get('user_email')
    album_id = request.GET.get('album_id')

    album = get_object_or_404(Album, pk=album_id)
    if request.user == album.user:
        user_to_remove = get_object_or_404(CustomUser, email=user_email)
        album.allowed_users.remove(user_to_remove)
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        else:
            return redirect('albums')
    else:
        raise Http404("Auth error")


@login_required
def add_tag(request):
    print("WE ARE ADDING NOW")
    new_tag = request.GET.get('tag')
    file_id = request.GET.get('file_id')

    file = get_object_or_404(Files, pk=file_id)
    if request.user == file.user:
        tag = Tag.objects.create(name=new_tag)
        file.tags.add(tag)
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        else:
            return redirect('gallery')
    else:
        raise Http404("Auth error")


# ТАМАРЕН КОД СНИЗУ
@login_required
def change_image_view(request):
    if request.method == 'GET':
        photo_url = request.GET.get('photo')
        photo_id = request.GET.get('id')
        if photo_url:
            return render(request, 'ChangeImage.html', {'photourl': photo_url, 'photoid': photo_id})


@login_required
def crop_image(request):
    if request.method == 'GET':
        photo_url = request.GET.get('photo')
        photo_id = request.GET.get('id')

        return render(request, 'CropImage.html', {'photourl': photo_url, 'photoid': photo_id})


@login_required
def add_text(request):
    if request.method == 'GET':
        photo_url = request.GET.get('photo')
        photo_id = request.GET.get('id')

        return render(request, 'AddTextToImage.html', {'photourl': photo_url, 'photoid': photo_id})


def save_text_on_image(request):
    textX = int(request.GET.get('textX'))
    textY = int(request.GET.get('textY'))
    textValue = request.GET.get('textValue')
    textColor = request.GET.get('textColor')
    textSize = round(float(request.GET.get('textSize')))
    id = request.GET.get('id')

    myModel = Files.objects.get(pk=id)

    original_photo = BytesIO(myModel.file.read())
    output_photo = BytesIO()

    image = Image.open(original_photo)

    font = ImageFont.load_default(size=textSize)
    width, height = image.size
    draw_text = ImageDraw.Draw(image)
    draw_text.text(((width * int(textX)) / 100, (height * int(textY)) / 100), textValue, fill=textColor, font=font)
    image.save(output_photo, 'png')

    myModel.file.save(f"{id}_withtext.png", ContentFile(output_photo.getvalue()))
    myModel.save()

    path = myModel.file.path
    
    image.close()
    original_photo.close()
    output_photo.close()
    
    return HttpResponse(json.dumps({'filepath': path[path.index("media") - 1::]}), content_type="application/json")


def save_cropped_image(request):
    print("WE ARE IN SAVING CROPPED IMAGE")
    x = int(request.GET.get('x'))
    y = int(request.GET.get('y'))
    height = int(request.GET.get('height'))
    width = int(request.GET.get('width'))
    id = request.GET.get('id')

    myModel = Files.objects.get(pk=id)

    original_photo = BytesIO(myModel.file.read())
    output_photo = BytesIO()

    image = Image.open(original_photo)

    image = image.crop((x, y, x + width, y + height))

    image.save(output_photo, 'png')


    myModel.file.save(f"{id}_cropped.jpg", ContentFile(output_photo.getvalue()))
    myModel.save()

    path = myModel.file.path
    
    original_photo.close()
    image.close()
    output_photo.close()
    
    return HttpResponse(json.dumps({'filepath': path[path.index("media") - 1::]}), content_type="application/json")


def save_image(request):
    if request.method == 'GET':
        bValue = request.GET.get('brightness')
        cValue = request.GET.get('contrast')
        rValue = request.GET.get('rotation')
        photo = request.GET.get('photo')
        id = request.GET.get('id')

        myModel = Files.objects.get(pk=id)
        
        print(myModel)

        original_photo = BytesIO(myModel.file.read())
        rotated_photo = BytesIO()

        image = Image.open(original_photo)

        enhBrightness = ImageEnhance.Brightness(image)

        image = enhBrightness.enhance(int(bValue) / 100)

        enhContrast = ImageEnhance.Contrast(image)
        image = enhContrast.enhance(int(cValue) / 100)

        image = image.rotate(-int(rValue))

        image.save(rotated_photo, "PNG")

        print("ПХОТО: " + myModel.title)

        myModel.file.save(f"{myModel.title}.png",
                          ContentFile(rotated_photo.getvalue()))
        myModel.save()

        path = myModel.file.path
        print("ПАТХ: " + path)
        
        image.close()
        original_photo.close()
        rotated_photo.close()
        return HttpResponse(json.dumps({'filepath': path[path.index("media") - 1::]}), content_type="application/json")
