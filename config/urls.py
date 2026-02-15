from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.shortcuts import render
from two_factor.admin import AdminSiteOTPRequired
from two_factor.urls import urlpatterns as tf_urls


admin.site.__class__ = AdminSiteOTPRequired

def home_view(request):
    return render(request, 'home.html')

urlpatterns = [
    path('', home_view, name='home'),
    path("", include('social_django.urls', namespace="social")),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('', include(tf_urls)),
]

if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
