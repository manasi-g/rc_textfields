from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.signup, name = 'signup'),
    path('SignIn/',views.signin, name = 'signin'),
    path('logout/',views.logout, name = 'logout'),
    path('quiz/',views.quiz, name ='quiz'),
    path('quiz_post/',views.quiz_post,name='quiz_post')
]