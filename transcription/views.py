from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.conf import settings
import threading
from rest_framework.permissions import AllowAny
import logging
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
import time
import traceback

from .models import Transcription, TranscriptionSegment
from .serializers import (
    TranscriptionSerializer,
    TranscriptionCreateSerializer,
    TranscriptionSegmentSerializer
)
from .services import TranscriptionService

logger = logging.getLogger(__name__)

# Create your views here.

class TranscriptionViewSet(viewsets.ModelViewSet):
    queryset = Transcription.objects.all()
    serializer_class = TranscriptionSerializer
    permission_classes = [AllowAny]  # For testing, we'll allow any access

    def get_serializer_class(self):
        if self.action == 'create':
            return TranscriptionCreateSerializer
        return TranscriptionSerializer

    def create(self, request, *args, **kwargs):
        try:
            start_time = time.time()
            audio_file = request.FILES.get('audio_file')
            language = request.data.get('language')  # Optional language parameter
            
            if not audio_file:
                return Response(
                    {"error": "No audio file provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate file size
            if audio_file.size > settings.MAX_AUDIO_SIZE:
                return Response(
                    {"error": f"File size exceeds maximum allowed size of {settings.MAX_AUDIO_SIZE / (1024*1024)}MB"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate file extension
            ext = audio_file.name.split('.')[-1].lower()
            if ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
                return Response(
                    {"error": f"Invalid file extension. Allowed extensions: {', '.join(settings.ALLOWED_AUDIO_EXTENSIONS)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create transcription object
            transcription = Transcription.objects.create(
                audio_file=audio_file,
                status='pending',
                language=language or 'auto'  # Use provided language or auto-detect
            )

            try:
                # Initialize service and transcribe
                service = TranscriptionService()
                service.transcribe_audio(
                    audio_path=transcription.audio_file.path,
                    transcription_id=transcription.id,
                    language=language  # Pass language to service
                )
                
                # Get the formatted transcription in JSON format
                result = service.get_transcription_text(transcription.id, format='json')
                
                return Response(result)

            except Exception as e:
                transcription.status = 'failed'
                transcription.error_message = str(e)
                transcription.save()
                return Response({
                    "error": "Transcription failed",
                    "details": str(e),
                    "transcription_id": transcription.id
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({
                "error": "Request failed",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        transcription = self.get_object()
        return Response({
            "id": transcription.id,
            "status": transcription.status,
            "duration": transcription.duration,
            "num_speakers": transcription.num_speakers,
            "language": transcription.language,
            "created_at": transcription.created_at,
            "updated_at": transcription.updated_at,
            "error_message": transcription.error_message
        })

    @action(detail=True, methods=['get'])
    def text(self, request, pk=None):
        try:
            transcription = self.get_object()
            service = TranscriptionService()
            format = request.query_params.get('format', 'text')
            
            if format not in ['text', 'json']:
                return Response({
                    "error": "Invalid format. Supported formats: text, json"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = service.get_transcription_text(transcription.id, format=format)
            
            if format == 'json':
                return Response(result)
            else:
                return Response({
                    "transcription_id": transcription.id,
                    "status": transcription.status,
                    "text": result,
                    "duration": transcription.duration,
                    "num_speakers": transcription.num_speakers,
                    "language": transcription.language
                })
        except Exception as e:
            return Response({
                "error": "Failed to get transcription text",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def segments(self, request, pk=None):
        transcription = self.get_object()
        segments = transcription.segments.all()
        serializer = TranscriptionSegmentSerializer(segments, many=True)
        return Response(serializer.data)
