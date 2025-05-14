from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

class ArticleCategory(models.Model):
    article_id = models.CharField(max_length=100)  # ID của bài viết từ MongoDB
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    confidence_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Article Categories'
        unique_together = ('article_id', 'category')

    def __str__(self):
        return f"Article {self.article_id} - {self.category.name}"

