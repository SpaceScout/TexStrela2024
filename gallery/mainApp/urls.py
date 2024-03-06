from django.urls import path
from . import views

urlpatterns = [
    path('gallery/', views.gallery_view, name="gallery"),
    path('', views.home_view, name="home"),
    path('albums/', views.albums_view, name="albums"),
    path('videos/', views.videos_view, name="videos"),
    path('bin/', views.bin_view, name="bin"),
    path('albums/<int:album_id>/', views.album_photos_view, name='album_photos'),
]
