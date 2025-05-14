from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, JsonResponse
from django.utils.feedgenerator import Rss201rev2Feed
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from .models import Category, ArticleCategory
from pymongo import MongoClient
from django.db.models import Count
from datetime import datetime

# Create your views here.
def home(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            logout(request) 
            messages.success(request, 'Logout Successful')
            return redirect('registration/login.html')
    # Nếu là admin -> vào trang admin
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/admin/')  # Django admin dashboard

    # Kết nối MongoDB
    client = MongoClient("mongodb+srv://phantonbasang:22677351@cluster0.vjd7ljz.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0")
    db = client['news_db']
    collection = db['vnexpress_articles']

    # Lấy tin tức nổi bật (tin mới nhất)
    featured_news = collection.find_one(
        sort=[('published_date', -1)]
    )

    # Lấy tất cả danh mục từ MongoDB
    categories = collection.distinct('category')
    
    # Tạo danh sách danh mục với thông tin chi tiết
    category_list = []
    for category in categories:
        # Đếm số bài viết trong danh mục
        article_count = collection.count_documents({'category': category})
        
        # Lấy 3 bài viết mới nhất trong danh mục
        latest_articles = list(collection.find(
            {'category': category},
            sort=[('published_date', -1)],
            limit=3
        ))
        
        category_list.append({
            'name': category,
            'slug': category.lower().replace(' ', '-'),
            'article_count': article_count,
            'latest_articles': latest_articles
        })

    # Thống kê
    total_articles = collection.count_documents({})
    total_categories = len(categories)
    last_update = datetime.now()

    context = {
        'featured_news': featured_news,
        'categories': category_list,
        'total_articles': total_articles,
        'total_categories': total_categories,
        'last_update': last_update,
        'show_favorites': request.user.is_authenticated  # Chỉ hiển thị mục yêu thích nếu đã đăng nhập
    }

    return render(request, 'home.html', context)

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect('base:login')
    else:
        form = UserCreationForm()
    return render(request,"registration/register.html",{"form":form})

def latest_news(request):
    client = MongoClient("mongodb+srv://phantonbasang:22677351@cluster0.vjd7ljz.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0")
    db = client['news_db']
    collection = db['vnexpress_articles']
    
    # Lấy danh sách tất cả danh mục
    categories = collection.distinct('category')
    
    # Lọc theo danh mục nếu có
    category = request.GET.get('category')
    if category:
        news = list(collection.find(
            {'category': category}
        ).sort('published_date', -1))
    else:
        news = list(collection.find().sort('published_date', -1))
    
    return render(request, 'news_rss_atlats/lastest_news.html', {
        'news': news,
        'categories': categories
    })

def all_articles(request):
    client = MongoClient("mongodb+srv://phantonbasang:22677351@cluster0.vjd7ljz.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0")
    db = client['news_db']
    collection = db['vnexpress_articles']

    # Lấy danh sách tất cả danh mục
    categories = collection.distinct('category')

    # Lọc theo danh mục nếu có
    category = request.GET.get('category')
    if category:
        articles = list(collection.find(
            {'category': category}
        ).sort('published_date', -1))
    else:
        articles = list(collection.find().sort('published_date', -1))

    # Phân trang: 10 bài/trang
    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'news_rss_atlats/all_articles.html', {
        'page_obj': page_obj,
        'categories': categories
    })

@login_required
def category_list(request):
    categories = Category.objects.annotate(
        article_count=Count('articlecategory')
    )
    return render(request, 'news_rss_atlats/category_list.html', {
        'categories': categories
    })

@login_required
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    
    # Lấy danh sách ID bài viết thuộc danh mục này
    article_ids = ArticleCategory.objects.filter(
        category=category
    ).values_list('article_id', flat=True)
    
    # Kết nối MongoDB và lấy thông tin bài viết
    client = MongoClient("mongodb+srv://phantonbasang:22677351@cluster0.vjd7ljz.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0")
    db = client['news_db']
    collection = db['vnexpress_articles']
    
    # Lấy thông tin bài viết từ MongoDB
    articles = list(collection.find(
        {'_id': {'$in': list(article_ids)}}
    ).sort('pub_date', -1))
    
    # Thêm thông tin confidence score cho mỗi bài viết
    for article in articles:
        article_category = ArticleCategory.objects.get(
            article_id=str(article['_id']),
            category=category
        )
        article['confidence_score'] = article_category.confidence_score
    
    return render(request, 'news_rss_atlats/category_detail.html', {
        'category': category,
        'articles': articles
    })

@login_required
def categorize_article(request, article_id):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        confidence_score = float(request.POST.get('confidence_score', 0.0))
        
        try:
            category = Category.objects.get(id=category_id)
            ArticleCategory.objects.update_or_create(
                article_id=article_id,
                category=category,
                defaults={'confidence_score': confidence_score}
            )
            return JsonResponse({'status': 'success'})
        except Category.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Category not found'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def categorized_articles(request):
    # Lấy danh sách ID bài viết đã được phân loại
    article_ids = ArticleCategory.objects.values_list('article_id', flat=True).distinct()
    
    # Kết nối MongoDB và lấy thông tin bài viết
    client = MongoClient("mongodb+srv://phantonbasang:22677351@cluster0.vjd7ljz.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0")
    db = client['news_db']
    collection = db['vnexpress_articles']
    
    # Lấy thông tin bài viết từ MongoDB
    articles = list(collection.find(
        {'_id': {'$in': list(article_ids)}}
    ).sort('pub_date', -1))
    
    # Thêm thông tin danh mục cho mỗi bài viết
    for article in articles:
        categories = ArticleCategory.objects.filter(article_id=str(article['_id']))
        article['categories'] = [
            {
                'name': ac.category.name,
                'confidence_score': ac.confidence_score
            }
            for ac in categories
        ]
    
    # Phân trang
    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Lấy danh sách tất cả danh mục để hiển thị bộ lọc
    categories = Category.objects.all()
    
    return render(request, 'news_rss_atlats/categorized_articles.html', {
        'page_obj': page_obj,
        'categories': categories
    })

