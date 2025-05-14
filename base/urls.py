from django.contrib import admin
from django.urls import path, include
from .views import home, register, latest_news, all_articles, category_list, category_detail, categorized_articles, categorize_article
from django.contrib.auth.views import LoginView, LogoutView

app_name = 'base'

urlpatterns = [
    path("", home, name="home"),
    path('accounts/', include("django.contrib.auth.urls")),
    path("login/", LoginView.as_view(template_name='registration/login.html'), name='login'),
    path("signup/", register, name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('latest_news/', latest_news, name='latest_news'),
    path('all_articles/', all_articles, name='all_articles'),
    path('categories/', category_list, name='category_list'),
    path('categories/<slug:slug>/', category_detail, name='category_detail'),
    path('categorized-articles/', categorized_articles, name='categorized_articles'),
    path('categorize-article/<str:article_id>/', categorize_article, name='categorize_article'),
    

]