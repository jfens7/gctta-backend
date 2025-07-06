# gctta_project/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # This line tells the project to look at our api/urls.py file
    # for any address that starts with 'api/'
    path('api/', include('api.urls')),
]