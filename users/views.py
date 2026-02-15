from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .turnstile import get_turnstile_site_key, is_turnstile_enabled
import sesame.utils
import os

User = get_user_model()

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request=request)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm(request=request)
    context = {
        'form': form,
        'turnstile_site_key': get_turnstile_site_key(),
        'turnstile_enabled': is_turnstile_enabled(),
    }
    return render(request, 'registration/register.html', context)

def login_view(request):
    if request.method == 'POST':
        # Check if this is a magic link request
        if 'magic_link' in request.POST:
            email = request.POST.get('email')
            if email:
                try:
                    user = User.objects.get(email=email)
                    # Generate magic link using sesame
                    token = sesame.utils.get_token(user)
                    magic_link = request.build_absolute_uri(
                        reverse('magic_login', kwargs={'token': token})
                    )
                    
                    # Send email with magic link
                    send_mail(
                        'Your Magic Login Link',
                        f'Click this link to log in: {magic_link}',
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                    messages.success(request, 'Magic link sent to your email!')
                except User.DoesNotExist:
                    messages.error(request, 'No account found with that email address.')
                except Exception as e:
                    messages.error(request, 'Error sending magic link. Please try again.')
            else:
                messages.error(request, 'Please enter your email address.')
        else:
            # Regular login form
            form = CustomAuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.email}!')
                return redirect('dashboard')  # Redirect to your dashboard or home page
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = CustomAuthenticationForm()
    context = {
        'form': form,
        'turnstile_site_key': get_turnstile_site_key(),
        'turnstile_enabled': is_turnstile_enabled(),
    }
    return render(request, 'registration/login.html', context)

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html', {'user': request.user})

def magic_login_view(request, token):
    """Handle magic link login"""
    user = sesame.utils.get_user(token)
    if user is not None:
        login(request, user)
        messages.success(request, f'Welcome back, {user.get_full_name() or user.email}!')
        return redirect('dashboard')
    else:
        messages.error(request, 'Invalid or expired magic link.')
        return redirect('login')

@login_required
def user_settings_view(request):
    return render(request, 'user_settings.html', {'user': request.user})
