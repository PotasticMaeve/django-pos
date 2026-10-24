from django.urls import re_path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import CustomTokenObtainPairView, RegisterView, LogoutView

urlpatterns = [
    re_path(r'^register/?$', RegisterView.as_view(), name='register'),
    re_path(r'^login/?$', CustomTokenObtainPairView.as_view(), name='token_obtain'),
    re_path(r'^token/refresh/?$', TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^token/verify/?$', TokenVerifyView.as_view(), name='token_verify'),
    re_path(r'^logout/?$', LogoutView.as_view(), name='logout'),
]