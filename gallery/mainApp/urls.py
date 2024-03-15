from django.urls import path, re_path
from . import views

urlpatterns = [
    path('gallery/', views.gallery_view, name="gallery"),
    re_path(r'^gallery/changeimage/$', views.change_image_view, name='user_change_image'),
    path('gallery/changeimage/save_image/', views.save_image),
    path('gallery/changeimage/crop_image/save_cropped_image/', views.save_cropped_image),
    path('gallery/changeimage/add_text/save_added_text/', views.save_text_on_image),
    re_path(r'^gallery/changeimage/crop_image/$', views.crop_image),
    re_path(r'^gallery/changeimage/add_text/$', views.add_text),
    path('delete/<int:file_id>/', views.delete_file, name="deleting"),
    path('download/<int:file_id>/', views.download_file_view, name="saving"),
    path('', views.home_view, name="home"),
    path('albums/', views.albums_view, name="albums"),
    path('videos/', views.videos_view, name="videos"),
    path('bin/', views.bin_view, name="bin"),
    path('albums/<int:album_id>/', views.album_view, name='album_files'),
    path('albums/add-photos/<int:album_id>/', views.add_files_to_album, name='photo_add'),
]
