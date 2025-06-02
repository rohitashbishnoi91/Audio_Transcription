from django.db import models
from django.core.validators import FileExtensionValidator
import os
import logging

logger = logging.getLogger(__name__)

def validate_audio_file(value):
    """Custom validator for audio files"""
    ext = os.path.splitext(value.name)[1].lower()
    allowed_extensions = ['.mp3', '.wav', '.m4a']
    
    if ext not in allowed_extensions:
        logger.warning(f"Invalid file extension: {ext} for file: {value.name}")
        raise models.ValidationError(
            f"Invalid file type. Only {', '.join(allowed_extensions)} files are allowed. "
            f"You uploaded: {value.name}"
        )

class Transcription(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    audio_file = models.FileField(
        upload_to='audio_files/',
        validators=[FileExtensionValidator(allowed_extensions=['wav', 'mp3', 'm4a', 'ogg'])]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    error_message = models.TextField(null=True, blank=True)
    language = models.CharField(max_length=10, default='en-US')
    num_speakers = models.IntegerField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)  # Duration in seconds

    def __str__(self):
        return f"Transcription {self.id} - {self.status}"

    def clean(self):
        """Additional validation before saving"""
        super().clean()
        if self.audio_file:
            # Check file size (limit to 10MB)
            if self.audio_file.size > 10 * 1024 * 1024:  # 10MB in bytes
                raise models.ValidationError(
                    "File size must be no more than 10MB"
                )

class TranscriptionSegment(models.Model):
    transcription = models.ForeignKey(Transcription, on_delete=models.CASCADE, related_name='segments')
    speaker = models.CharField(max_length=50)  # Speaker identifier (e.g., "SPEAKER_1", "SPEAKER_2")
    speaker_label = models.CharField(max_length=50, null=True, blank=True)  # Optional human-readable label
    text = models.TextField()
    start_time = models.FloatField()  # Start time in seconds
    end_time = models.FloatField()    # End time in seconds
    confidence = models.FloatField(null=True, blank=True)  # Confidence score for this segment
    language = models.CharField(max_length=10, null=True, blank=True)  # Language of this segment

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.speaker} ({self.start_time:.2f}-{self.end_time:.2f}): {self.text[:50]}..."
