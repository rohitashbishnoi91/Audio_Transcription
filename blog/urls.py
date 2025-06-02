from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BlogPostViewSet, test_endpoint, health_check
from django.http import JsonResponse

def debug_urls(request):
    """Debug endpoint to show all available URLs"""
    urls = [
        '/api/blog/health/',
        '/api/blog/test/',
        '/api/blog/debug/',
        '/api/blog/posts/',
        '/api/blog/posts/generate_titles/',
    ]
    return JsonResponse({'available_urls': urls})

router = DefaultRouter()
router.register(r'posts', BlogPostViewSet, basename='blogpost')

urlpatterns = [
    path('health/', health_check, name='health-check'),
    path('debug/', debug_urls, name='debug-urls'),
    path('test/', test_endpoint, name='test-endpoint'),
    path('', include(router.urls)),
] 