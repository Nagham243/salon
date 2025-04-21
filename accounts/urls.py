from django.urls import path
from . import views
from django.conf import settings


urlpatterns = [
    path('signin', views.signin, name='signin'),
    path('signup', views.signup, name='signup'),
    path('signout', views.signout, name='signout'),
    path('verify-otp', views.verify_otp, name='verify_otp'),  # Add this line
]
