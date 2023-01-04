from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('stats/', include('stats.urls')),
    path('accounts/login/', auth_views.LoginView.as_view()),
    path('admin/', admin.site.urls),
]
