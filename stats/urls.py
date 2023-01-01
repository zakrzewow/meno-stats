from django.urls import path, register_converter

from . import views, converters

register_converter(converters.DateConverter, 'date')

app_name = 'stats'
urlpatterns = [
    path('', views.index, name='index'),
    path('following', views.following, name='following'),
    path('<int:aid>/<date:activity_date>', views.detail, name='detail'),
]
