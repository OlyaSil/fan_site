from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
import datetime


class Advertisement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = RichTextField()
    media = models.FileField(upload_to='media/', blank=True, null=True)
    category_choices = [
        ('Танки', 'Танки'),
        ('Хилы', 'Хилы'),
        ('ДД', 'ДД'),
        ('Торговцы', 'Торговцы'),
        ('Гилдмастеры', 'Гилдмастеры'),
        ('Квестгиверы', 'Квестгиверы'),
        ('Кузнецы', 'Кузнецы'),
        ('Кожевники', 'Кожевники'),
        ('Зельевары', 'Зельевары'),
        ('Мастера заклинаний', 'Мастера заклинаний'),
    ]
    category = models.CharField(max_length=50, choices=category_choices)

    is_published = models.BooleanField(default=False)

    likes = models.ManyToManyField(User, related_name='liked_advertisements', blank=True)

    def like(self, user):
        self.likes.add(user)

    def unlike(self, user):
        self.likes.remove(user)


class Response(models.Model):
    advertisement = models.ForeignKey('Advertisement', related_name='responses', on_delete=models.CASCADE)
    respondent = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return f'{self.content[:50]}... by {self.respondent.username}'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    confirmation_code = models.CharField(max_length=20)

    private_page_info = models.TextField(default='')

    def get_private_page(self):
        return self.private_page_info

class OneTimeCode(models.Model):
    code = models.CharField(max_length=6)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Response(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ]
    advertisement = models.ForeignKey(Advertisement, related_name='responses', on_delete=models.CASCADE)
    respondent = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f'{self.content[:50]}... by {self.respondent.username}'


class NewsletterSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    is_subscribed = models.BooleanField(default=True)

    def __str__(self):
        return self.email