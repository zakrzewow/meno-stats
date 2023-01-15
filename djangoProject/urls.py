from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include

urlpatterns = [
    path('stats/', include('stats.urls')),
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('stats/', permanent=True)),
]
