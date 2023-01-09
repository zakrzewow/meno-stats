from django.urls import path, register_converter

from . import views, converters

register_converter(converters.DateConverter, 'date')


app_name = 'stats'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('following', views.FollowingView.as_view(), name='following'),
    path('unfollow/<int:aid>', views.UnfollowView.as_view(), name='unfollow'),
    path('<int:aid>/<date:activity_date>', views.detail, name='detail'),
    path('export/<int:aid>', views.ExportAsXmlView.as_view(), name='export'),
    path('accounts/login', views.MyLoginView.as_view(), name='login'),
    path('accounts/logout', views.logout, name='logout'),
    path('accounts/register', views.RegistrationView.as_view(), name='register'),
    path('accounts/activate/<uidb64>/<token>', views.AccountActivationView.as_view(), name='activate'),
]
