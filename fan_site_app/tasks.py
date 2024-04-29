from celery import shared_task
from django.core.mail import send_mail
from .models import NewsletterSubscription, Advertisement
from django.utils import timezone
from datetime import timedelta

@shared_task
def send_weekly_advertisements():
    one_week_ago = timezone.now() - timedelta(days=7)
    subscriptions = NewsletterSubscription.objects.filter(active=True)

    for subscription in subscriptions:
        advertisements = Advertisement.objects.filter(
            category=subscription.category,
            created_at__gte=one_week_ago
        )

        if advertisements.exists():
            subject = f'Новые объявления в категории {subscription.category}'
            message = "\n".join([ad.title for ad in advertisements])
            send_mail(
                subject,
                message,
                'from@example.com',
                [subscription.user.email],
                fail_silently=False,
            )
