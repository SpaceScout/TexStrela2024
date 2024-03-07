from django.urls import path, re_path
from . import views

urlpatterns = [
    path('gallery/', views.gallery_view, name="user_gallery"),
    re_path(r'^gallery/changeimage/$', views.change_image_view, name='user_change_image'),
    path('', views.home_view, name="home"),
    # url(r'^pay/summary/(?P<value>\d+)/$', views.pay_summary, name='pay_summary')),
]
