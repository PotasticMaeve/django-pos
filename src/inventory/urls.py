from .views import ProductAPIView
from django.urls import re_path

urlpatterns = [
    re_path(r'^(?:|/)$', ProductAPIView.as_view(), name='product-list'),
]