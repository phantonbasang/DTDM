from django.contrib import admin
from django.urls import path, include
from .views import home, signup, latest_news,all_articles
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("", home, name="home"),
    path('accounts/',include("django.contrib.auth.urls")),
    path("signup/",signup, name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('latest_news/', latest_news, name='latest_news'),
    path('all_articles/', all_articles, name='all_articles'),
]