from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('advertisement/add/', add_advertisement, name='add_advertisement'),
    path('advertisement/<int:advertisement_id>/', advertisement_detail, name='advertisement_detail'),
    path('advertisement/<int:advertisement_id>/edit/', edit_advertisement, name='edit_advertisement'),
    path('advertisement/<int:advertisement_id>/delete/', delete_advertisement, name='delete_advertisement'),
    path('advertisement/<int:advertisement_id>/response/add/', add_response, name='add_response'),
    path('advertisement/<int:advertisement_id>/response/<int:response_id>/edit/', edit_response, name='edit_response'),
    path('advertisement/<int:advertisement_id>/response/<int:response_id>/delete/', delete_response, name='delete_response'),
    path('advertisement/like/<int:advertisement_id>/', like_advertisement, name='like_advertisement'),
    path('all_advertisements/', all_advertisements, name='all_advertisements'),
    path('register/', register, name='register'),
    path('activate/<uidb64>/<token>/', activate_account, name='activate_account'),
    path('login_with_code/', login_with_code_view, name='login_with_code'),
    path('invalid_code/', invalid_code, name='invalid_code'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('my_responses/', my_responses, name='my_responses'),
    path('accept_response/<int:response_id>/', accept_response, name='accept_response'),
    path('delete_response/<int:response_id>/', delete_response, name='delete_response'),
    path('send_newsletter/', send_newsletter, name='send_newsletter'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
