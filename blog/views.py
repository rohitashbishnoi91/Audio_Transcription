from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils.text import slugify
import logging
from django.http import JsonResponse
from django.core.exceptions import ValidationError

from .models import BlogPost, TitleSuggestion
from .serializers import (
    BlogPostSerializer,
    BlogPostCreateSerializer,
    TitleSuggestionSerializer,
    TitleSuggestionRequestSerializer
)
from .services import TitleSuggestionService, TitleGenerationService

# Set up logging
logger = logging.getLogger(__name__)

@api_view(['GET'])
def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({
        'status': 'ok',
        'message': 'Server is running'
    })

@api_view(['POST'])
def test_endpoint(request):
    """Test endpoint for POST requests"""
    logger.info(f"Received test request with data: {request.data}")
    return Response({
        "message": "Test endpoint working!",
        "received_data": request.data
    })

class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return BlogPostCreateSerializer
        return BlogPostSerializer

    def create(self, request, *args, **kwargs):
        try:
            # Get content from request
            content = request.data.get('content')
            if not content:
                return Response(
                    {"error": "No content provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create blog post
            blog_post = BlogPost.objects.create(
                content=content,
                status='draft'
            )

            # Generate title suggestions
            try:
                service = TitleGenerationService()
                titles = service.generate_titles(
                    content=content,
                    num_titles=3,
                    max_length=50
                )
                
                # Update blog post with first title suggestion
                blog_post.title = titles[0]
                blog_post.save()
                
                return Response({
                    "id": blog_post.id,
                    "title": blog_post.title,
                    "title_suggestions": titles,
                    "status": blog_post.status,
                    "created_at": blog_post.created_at
                })

            except Exception as e:
                blog_post.status = 'failed'
                blog_post.error_message = str(e)
                blog_post.save()
                return Response({
                    "error": "Title generation failed",
                    "details": str(e),
                    "blog_post_id": blog_post.id
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({
                "error": "Request failed",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def generate_titles(self, request, pk=None):
        """Generate new title suggestions for an existing blog post."""
        try:
            blog_post = self.get_object()
            
            # Get number of titles to generate (default: 3)
            num_titles = int(request.data.get('num_titles', 3))
            if num_titles < 1 or num_titles > 10:
                return Response(
                    {"error": "Number of titles must be between 1 and 10"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate title suggestions
            service = TitleGenerationService()
            titles = service.generate_titles(
                content=blog_post.content,
                num_titles=num_titles,
                max_length=50
            )
            
            return Response({
                "blog_post_id": blog_post.id,
                "current_title": blog_post.title,
                "title_suggestions": titles
            })
            
        except Exception as e:
            return Response({
                "error": "Failed to generate titles",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def update_title(self, request, pk=None):
        """Update the blog post title."""
        try:
            blog_post = self.get_object()
            new_title = request.data.get('title')
            
            if not new_title:
                return Response(
                    {"error": "No title provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            blog_post.title = new_title
            blog_post.save()
            
            return Response({
                "id": blog_post.id,
                "title": blog_post.title,
                "status": blog_post.status,
                "updated_at": blog_post.updated_at
            })
            
        except Exception as e:
            return Response({
                "error": "Failed to update title",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def suggest_titles(self, request, pk=None):
        blog_post = self.get_object()
        service = TitleSuggestionService()
        
        try:
            titles = service.generate_titles(blog_post.content, blog_post)
            suggestions = blog_post.title_suggestions.all()
            serializer = TitleSuggestionSerializer(suggestions, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def generate_titles(self, request):
        logger.info("Received request for title generation")
        logger.info(f"Request data: {request.data}")
        
        try:
            # Log the incoming request
            logger.info("Validating request data")
            serializer = TitleSuggestionRequestSerializer(data=request.data)
            
            if not serializer.is_valid():
                logger.error(f"Validation error: {serializer.errors}")
                return Response(
                    {'error': 'Invalid data', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info("Request data validated successfully")
            
            # Initialize the service
            logger.info("Initializing TitleSuggestionService")
            service = TitleSuggestionService()
            
            # Generate titles
            logger.info("Generating titles")
            content = serializer.validated_data['content']
            titles = service.generate_titles(content)
            
            logger.info(f"Generated titles: {titles}")
            return Response({'suggestions': titles})
            
        except Exception as e:
            logger.error(f"Error in generate_titles: {str(e)}", exc_info=True)
            return Response(
                {
                    'error': 'An error occurred while generating titles',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
