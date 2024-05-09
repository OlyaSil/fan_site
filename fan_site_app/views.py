from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import *
from .forms import *
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mass_mail, send_mail
from celery import shared_task


def send_confirmation_email(user):
    code = get_random_string(length=6)
    OneTimeCode.objects.create(code=code, user=user)
    subject = 'Печать Подтверждения'
    message = render_to_string('registration/confirmation_email.html', {
        'user': user,
        'code': code,
    })
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            send_confirmation_email(user)
            messages.success(request, 'Магическая печать отправлена вам на почту для подтверждения регистрации.')
            return redirect('activate_account')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def activate_account(request):
    if request.method == 'POST':
        form = ActivationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['temporary_code']
            user_code = OneTimeCode.objects.filter(code=code).first()
            if user_code and not user_code.user.is_active:
                user = user_code.user
                user.is_active = True
                user.save()
                login(request, user)
                messages.success(request, 'Ваши магические силы активированы, теперь вы можете войти в портал.')
                return redirect('home')
            else:
                messages.error(request, 'Неверная печать или аккаунт уже открыт к миру магии.')
    else:
        form = ActivationForm()
    return render(request, 'registration/activate_account.html', {'form': form})


def login_with_code_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        code = request.POST['code']
        if OneTimeCode.objects.filter(code=code, user__username=username).exists():
            user = authenticate(request, username=username)
            if user is not None:
                login(request, user)
                return redirect('all_advertisements')
        else:
            messages.error(request, 'Магическая печать недействительна.')
            return redirect('invalid_code')


def invalid_code(request):
    return render(request, 'registration/invalid_code.html')


@login_required
def all_advertisements(request):
    advertisements = Advertisement.objects.all()
    for advertisement in advertisements:
        advertisement.like_count = advertisement.likes.count()
    return render(request, 'all_advertisements.html', {'advertisements': advertisements})


@login_required
def like_advertisement(request, advertisement_id):
    advertisement = get_object_or_404(Advertisement, pk=advertisement_id)
    advertisement.likes.add(request.user)
    advertisement.like_count = advertisement.likes.count()
    advertisement.save()
    return HttpResponseRedirect(reverse('advertisement_detail', args=(advertisement_id,)))


@login_required
def advertisement_detail(request, advertisement_id):
    advertisement = get_object_or_404(Advertisement, pk=advertisement_id)
    return render(request, 'advertisement_detail.html', {'advertisement': advertisement})


@login_required
def my_messages(request):
    responses = Response.objects.filter(respondent=request.user)
    return render(request, 'my_messages.html', {'responses': responses})


@login_required
def add_response(request, advertisement_id):
    if request.method == 'POST':
        form = ResponseForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            if content:
                advertisement = Advertisement.objects.get(pk=advertisement_id)
                Response.objects.create(advertisement=advertisement, respondent=request.user, content=content)
                send_mail(
                    'Новый отклик получен',
                    f'Вы получили новый отклик: {content}',
                    settings.DEFAULT_FROM_EMAIL,
                    [advertisement.user.email],
                    fail_silently=False,
                )
                messages.success(request, 'Ваш отклик отправлен в таинственные дали.')
                return redirect('advertisement_detail', advertisement_id=advertisement_id)
            else:
                messages.error(request, 'Текст отклика не может быть пустым.')
    else:
        advertisement = Advertisement.objects.get(pk=advertisement_id)
        form = ResponseForm()
    character_name = request.user.username
    return render(request, 'add_response.html',
                  {'advertisement': advertisement, 'form': form, 'character_name': character_name})


@login_required
def add_advertisement(request):
    if request.method == 'POST':
        form = AdvertisementForm(request.POST, request.FILES)
        if form.is_valid():
            advertisement = form.save(commit=False)
            advertisement.user = request.user
            advertisement.save()
            return redirect('all_advertisements')
    else:
        form = AdvertisementForm()
    return render(request, 'add_advertisement.html', {'form': form})


@login_required
def edit_advertisement(request, advertisement_id):
    advertisement = get_object_or_404(Advertisement, pk=advertisement_id)
    if request.user == advertisement.user:
        if request.method == 'POST':
            form = AdvertisementForm(request.POST, request.FILES, instance=advertisement)
            if form.is_valid():
                form.save()
                messages.success(request, 'Заклинание вашего объявления успешно переплетено заново.')
                return redirect('advertisement_detail', advertisement_id=advertisement_id)
        else:
            form = AdvertisementForm(instance=advertisement)
        return render(request, 'edit_advertisement.html', {'form': form})
    else:
        messages.error(request, 'Вы не обладаете магией, чтобы изменить это объявление.')
        return redirect('advertisement_detail', advertisement_id=advertisement_id)

@login_required
def delete_advertisement(request, advertisement_id):
    advertisement = get_object_or_404(Advertisement, pk=advertisement_id)
    if request.user == advertisement.user:
        advertisement.delete()
        messages.success(request, 'Объявление растворено в воздухе.')
    else:
        messages.error(request, 'У вас нет силы разрушить это объявление.')
    return redirect('all_advertisements')


@login_required
def edit_response(request, response_id):
    response = get_object_or_404(Response, pk=response_id)
    advertisement_id = response.advertisement.pk
    if request.user == response.respondent:
        if request.method == 'POST':
            form = ResponseForm(request.POST, instance=response)
            if form.is_valid():
                form.save()
                messages.success(request, 'Ваше послание было изменено с магией знаний.')
                return redirect('advertisement_detail', advertisement_id=advertisement_id)
        else:
            form = ResponseForm(instance=response)
        return render(request, 'edit_response.html', {'form': form})
    else:
        messages.error(request, 'Вы не обладаете правом изменять этот магический ответ.')
        return redirect('advertisement_detail', advertisement_id=advertisement_id)


def invalid_login(request):
    return render(request, 'registration/invalid_login.html')


@login_required
def delete_response(request, advertisement_id, response_id):
    response = get_object_or_404(Response, pk=response_id)
    if request.user == response.respondent:
        response.delete()
        messages.success(request, 'Ответ испарился, как и его следы.')
    else:
        messages.error(request, 'Этот ответ защищен от ваших чар.')
    return redirect('advertisement_detail', advertisement_id=advertisement_id)

@login_required
def add_response(request, advertisement_id):
    advertisement = get_object_or_404(Advertisement, pk=advertisement_id)
    if request.method == 'POST':
        form = ResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.advertisement = advertisement
            response.respondent = request.user
            response.save()
            send_mail(
                'Вы получили новый отклик',
                f'Сова принесла вам добрые вести: {response.content}',
                settings.DEFAULT_FROM_EMAIL,
                [advertisement.user.email],
                fail_silently=False,
            )
            messages.success(request, 'Ваш отклик отправлен и ждет рассмотрения магистра объявлений.')
            return redirect('advertisement_detail', advertisement_id=advertisement_id)
    else:
        form = ResponseForm()
    return render(request, 'add_response.html', {'form': form, 'advertisement': advertisement})

@login_required
def my_responses(request):
    user = request.user
    advertisements = Advertisement.objects.filter(user=user).prefetch_related('responses__respondent')
    return render(request, 'my_responses.html', {'advertisements': advertisements})

@login_required
def accept_response(request, response_id):
    response = Response.objects.get(pk=response_id)
    response.accepted = True
    response.save()
    return redirect('my_responses')

@login_required
def delete_response(request, response_id):
    response = Response.objects.get(pk=response_id)
    response.delete()
    return redirect('my_responses')

def subscribe_to_newsletter(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Поздравляем! Вы подписаны на волшебные письма из нашего королевства.')
            return redirect('home')
    else:
        form = NewsletterForm()
    return render(request, 'subscribe.html', {'form': form})

def unsubscribe_from_newsletter(request, user_id):
    subscription = NewsletterSubscription.objects.get(user__id=user_id)
    subscription.is_subscribed = False
    subscription.save()
    messages.success(request, 'Вы отписались от волшебных рассылок.')
    return redirect('all_advertisements')


def send_newsletter():
    subscribers = NewsletterSubscription.objects.filter(is_subscribed=True)
    messages = []
    for subscriber in subscribers:
        message = ('Новости Недели', f'Внимание, жители! Вот свежие новости за неделю для вас, {subscriber.user.username}', 'from@example.com', [subscriber.email])
        messages.append(message)

    send_mass_mail(messages, fail_silently=False)

@shared_task
def send_newsletter():
    subscribers = NewsletterSubscription.objects.filter(is_subscribed=True)
    for subscriber in subscribers:
        send_mail(
            'Новости от Magic World',
            'Подборка самых свежих и чарующих новостей недели для вас, благородные маги и воины!',
            'silakova-o.a@yandex.ru',
            [subscriber.email],
            fail_silently=False,
        )
