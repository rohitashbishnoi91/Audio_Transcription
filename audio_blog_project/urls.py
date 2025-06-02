"""
URL configuration for audio_blog_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def home(request):
    """Home endpoint to show available API endpoints"""
    endpoints = {
        'blog': {
            'test': '/api/blog/test/',
            'debug': '/api/blog/debug/',
            'posts': '/api/blog/posts/',
            'generate_titles': '/api/blog/posts/generate_titles/',
        },
        'transcription': {
            'transcribe': '/api/transcription/transcriptions/',
        }
    }
    return JsonResponse(endpoints)

# URL patterns
urlpatterns = [
    # Home route - must be first
    re_path(r'^$', home, name='home'),  # Changed to re_path for root URL
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API routes
    path('api/blog/', include('blog.urls')),
    path('api/transcription/', include('transcription.urls')),
    path('api-auth/', include('rest_framework.urls')),
]

# Add media URLs in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
