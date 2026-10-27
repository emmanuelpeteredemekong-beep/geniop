from django.db import models
from django.contrib.auth.models import User

def get_price(count):
    if count <= 200:
        return 500
    elif count <= 500:
        return 1000
    elif count <= 1000:
        return 1500
    elif count <= 2000:
        return 3000
    elif count <= 3500:
        return 5000
    elif count <= 4999:
        return 7500
    else:
        return 10000

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    caption = models.TextField(blank=True)
    image = models.ImageField(upload_to='posts/')
    location = models.CharField(max_length=100, blank=True, default='Awka, NG')
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.caption[:30]}"

class SalesReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='reports/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
