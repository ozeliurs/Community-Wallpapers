from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('image/<int:pk>/', views.ImageDetailView.as_view(), name='image_detail'),
    path('upload/', views.upload_image, name='upload_image'),
    path('upload/url/', views.upload_image_url, name='upload_image_url'),
    path('review/', views.PendingReviewListView.as_view(), name='pending_review'),
    path('approve/<int:pk>/', views.approve_image, name='approve_image'),
    path('image-of-the-day/', views.image_of_the_day, name='image_of_the_day'),
    path('api/image-of-the-day/', views.image_of_the_day_api, name='image_of_the_day_api'),
    path('image-of-the-day.jpeg', views.image_of_the_day_direct, name='image_of_the_day_direct'),
]
