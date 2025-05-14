from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, JsonResponse
from django.utils.feedgenerator import Rss201rev2Feed
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator

# Create your views here.
@login_required
def home(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            logout(request) 
            messages.success(request, 'Logout Successful')
            return redirect('registration/login.html')
    # Nếu là admin -> vào trang admin
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/admin/')  # Django admin dashboard

    # Nếu là user thường -> vào trang home
    return render(request, "home.html")
def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect('base:login')
    else:
        form = UserCreationForm()
    return render(request,"registration/signup.html",{"form":form})


## lấy ra các bài báo mới nhất
from pymongo import MongoClient

def latest_news(request):
    client = MongoClient("mongodb+srv://root:12345@cluster0.p1zfuq5.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0")
    db = client['news_db']
    collection = db['vnexpress_articles']
    news = list(collection.find().sort('published', -1))
    return render(request, 'news_rss_atlats/lastest_news.html', {'news': news})



from django.core.paginator import Paginator
from django.shortcuts import render
from pymongo import MongoClient

def all_articles(request):
    client = MongoClient("mongodb+srv://root:12345@cluster0.p1zfuq5.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0")
    db = client['news_db']
    collection = db['vnexpress_articles']

    # Lấy tất cả bài báo, sắp xếp mới nhất trước
    articles = list(collection.find().sort('pub_date', -1))

    # Phân trang: 10 bài/trang
    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'news_rss_atlats/all_articles.html', {'page_obj': page_obj})