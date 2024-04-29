from django.contrib import admin
from .models import NewsletterSubscription

@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_subscribed', 'user']
    list_filter = ['is_subscribed']
    search_fields = ['email', 'user__username']
