from rest_framework import serializers
from .models import BlogPost, TitleSuggestion

class TitleSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TitleSuggestion
        fields = ['suggested_title', 'confidence_score', 'is_selected']

class BlogPostSerializer(serializers.ModelSerializer):
    title_suggestions = TitleSuggestionSerializer(many=True, read_only=True)
    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'content', 'status',
            'created_at', 'updated_at', 'error_message', 'slug', 'title_suggestions'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'error_message', 'slug', 'title_suggestions']

class BlogPostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = ['content']
        extra_kwargs = {
            'content': {'required': True}
        }

    def validate_content(self, value):
        """Validate the content field."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Content cannot be empty")
        if len(value) < 50:
            raise serializers.ValidationError("Content must be at least 50 characters long")
        return value

class TitleSuggestionRequestSerializer(serializers.Serializer):
    content = serializers.CharField(required=True) 