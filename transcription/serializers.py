from rest_framework import serializers
from .models import Transcription, TranscriptionSegment

class TranscriptionSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptionSegment
        fields = ['speaker', 'text', 'start_time', 'end_time', 'confidence']

class TranscriptionSerializer(serializers.ModelSerializer):
    segments = TranscriptionSegmentSerializer(many=True, read_only=True)

    class Meta:
        model = Transcription
        fields = ['id', 'audio_file', 'language', 'status', 'created_at', 'segments', 'error_message']
        read_only_fields = ['id', 'status', 'created_at', 'segments', 'error_message']

class TranscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcription
        fields = ['audio_file', 'language'] 