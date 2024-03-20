from django.urls import path, re_path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home_view, name="home"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('gallery/', views.gallery_view, name="gallery"),
    path('albums/', views.albums_view, name="albums"),
    path('videos/', views.videos_view, name="videos"),
    path('albums/<int:album_id>/', views.album_view, name='album_files'),
    path('show_image/<int:file_id>/', views.show_image, name='show_image'),

    re_path(r'^gallery/changeimage/$', views.change_image_view, name='user_change_image'),
    path('gallery/changeimage/save_image/', views.save_image),
    path('gallery/changeimage/crop_image/save_cropped_image/', views.save_cropped_image),
    path('gallery/changeimage/add_text/save_added_text/', views.save_text_on_image),
    re_path(r'^gallery/changeimage/crop_image/$', views.crop_image),
    re_path(r'^gallery/changeimage/add_text/$', views.add_text),

    path('delete/<int:file_id>/', views.delete_file, name="deleting"),
    path('album/<int:album_id>/delete/<int:file_id>/', views.delete_file, name="deleting_file_from_album"),
    path('download/<int:file_id>/', views.download_file_view, name="saving"),
    path('albums/<int:album_id>/download/', views.download_album, name='download_album'),

    re_path(r'^add-user-to-album/$', views.add_user_to_album, name="adding_user"),
    re_path(r'^delete-user-from-album/$', views.delete_user_from_album, name="deleting_user"),
    path('albums/add-photos/<int:album_id>/', views.add_files_to_album, name='photo_add'),
    re_path(r'tags/add-tag/$', views.add_tag, name='tag_add'),
]
