"""
URL configuration for fliptrouble project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include, re_path
from django.views.generic.base import RedirectView
from app_fliptrouble import views

urlpatterns = [
    path('', RedirectView.as_view(url='/app_fliptrouble/')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('app_fliptrouble/', include('app_fliptrouble.urls')),  
]
handler404 = 'app_fliptrouble.views.custom_404'