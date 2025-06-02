from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
import logging

logger = logging.getLogger(__name__)

class BlogPost(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('failed', 'Failed')
    ]

    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        """Override save to generate slug from title."""
        if self.title and not self.slug:
            self.slug = slugify(self.title)
            # Ensure slug uniqueness
            base_slug = self.slug
            counter = 1
            while BlogPost.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"Blog Post {self.id}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['slug'])
        ]

class TitleSuggestion(models.Model):
    blog_post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='title_suggestions'
    )
    suggested_title = models.CharField(max_length=200)
    confidence_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_selected = models.BooleanField(default=False)

    class Meta:
        ordering = ['-confidence_score']

    def __str__(self):
        return f"Suggestion for {self.blog_post.title}"
