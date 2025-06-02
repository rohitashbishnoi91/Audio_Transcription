import os
import logging
import time
import traceback
import torch
import torchaudio
from django.conf import settings
from pyannote.audio import Pipeline
from pyannote.core import Segment
import whisper
from .models import Transcription, TranscriptionSegment
import huggingface_hub
import tempfile
import shutil
from huggingface_hub import snapshot_download, HfFolder
import requests
from requests.exceptions import RequestException
import concurrent.futures
import atexit
import gc
import json

logger = logging.getLogger(__name__)

class TranscriptionService:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TranscriptionService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if TranscriptionService._initialized:
            logger.info("TranscriptionService already initialized, skipping initialization")
            return
            
        try:
            logger.info("Initializing TranscriptionService...")
            
            # Create cache directory
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'model_cache')
            os.makedirs(cache_dir, exist_ok=True)
            logger.info(f"Created cache directory at: {cache_dir}")
            
            # Configure Hugging Face cache paths
            os.environ['HF_HOME'] = cache_dir
            os.environ['TRANSFORMERS_CACHE'] = os.path.join(cache_dir, 'transformers')
            os.environ['HF_DATASETS_CACHE'] = os.path.join(cache_dir, 'datasets')
            logger.info("Configured Hugging Face cache paths")
            
            # Verify token before proceeding
            token = settings.PYANNOTE_AUTH_TOKEN
            if not token:
                raise ValueError("PYANNOTE_AUTH_TOKEN not set in settings")
            
            # Test token with Hugging Face API
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                "https://huggingface.co/api/whoami",
                headers=headers,
                timeout=10
            )
            if response.status_code != 200:
                error_msg = f"Token verification failed with {response.status_code} {response.reason}"
                logger.error(error_msg)
                logger.error(f"Response content: {response.text}")
                raise ValueError(f"Invalid or expired Hugging Face token. Please check your token and ensure it has the correct permissions.")
            
            # Set token in HfFolder for all Hugging Face operations
            HfFolder.save_token(token)
            logger.info("Token verified and set in HfFolder")
            
            # Initialize Whisper model
            logger.info("Initializing Whisper model...")
            try:
                # Force garbage collection before loading model
                gc.collect()
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
                
                # Create a temporary directory for model download
                with tempfile.TemporaryDirectory() as temp_dir:
                    model_path = os.path.join(temp_dir, 'base.pt')
                    self.whisper_model = whisper.load_model(
                        "base",
                        download_root=temp_dir,
                        device='cuda' if torch.cuda.is_available() else 'cpu'
                    )
                    # Move the model to the final location
                    final_path = os.path.join(cache_dir, 'whisper', 'base.pt')
                    os.makedirs(os.path.dirname(final_path), exist_ok=True)
                    shutil.move(model_path, final_path)
                logger.info("Whisper model initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Whisper model: {str(e)}")
                raise
            
            # Initialize diarization pipeline
            logger.info("Initializing diarization pipeline...")
            try:
                # Set timeout for requests
                huggingface_hub.constants.HF_HUB_DOWNLOAD_TIMEOUT = 300  # 5 minutes
                
                # Download model files with timeout
                logger.info("Downloading model files...")
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        snapshot_download,
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=token,
                        cache_dir=os.path.join(cache_dir, 'pyannote'),
                        local_files_only=False
                    )
                    try:
                        model_path = future.result(timeout=300)  # 5 minutes timeout
                        logger.info(f"Model files downloaded to: {model_path}")
                    except concurrent.futures.TimeoutError:
                        raise Exception("Model download timed out after 5 minutes")
                    except Exception as e:
                        if "401" in str(e):
                            raise Exception("Invalid or expired Hugging Face token. Please check your token and ensure it has the correct permissions.")
                        raise Exception(f"Model download failed: {str(e)}")
                
                # Initialize the pipeline with the downloaded model
                logger.info("Loading pipeline from downloaded model...")
                self.diarization_pipeline = Pipeline.from_pretrained(
                    model_path,
                    use_auth_token=token
                )
                
                # Test the pipeline with a dummy input
                logger.info("Testing pipeline initialization...")
                dummy_waveform = torch.zeros((1, 16000))  # 1 second of silence
                dummy_sample_rate = 16000
                test_result = self.diarization_pipeline(
                    {"waveform": dummy_waveform, "sample_rate": dummy_sample_rate},
                    min_speakers=1,
                    max_speakers=2
                )
                logger.info("Pipeline test successful")
                
            except Exception as e:
                logger.error(f"Error initializing diarization pipeline: {str(e)}\n{traceback.format_exc()}")
                if "401" in str(e):
                    raise Exception("Invalid or expired Hugging Face token. Please check your token and ensure it has the correct permissions.")
                raise Exception(f"Diarization pipeline initialization failed: {str(e)}")
            
            # Move models to GPU if available
            if torch.cuda.is_available():
                logger.info("Using GPU for models")
                self.diarization_pipeline = self.diarization_pipeline.to(torch.device("cuda"))
            else:
                logger.info("Using CPU for models")
            
            logger.info("All models initialized successfully")
            TranscriptionService._initialized = True
            
            # Register cleanup function
            atexit.register(self.cleanup)
            
        except Exception as e:
            error_msg = f"Error loading models: {str(e)}"
            logger.error(error_msg)
            if "401" in str(e):
                error_msg += "\nPlease make sure you have:\n1. Accepted the terms of use at https://huggingface.co/pyannote/speaker-diarization-3.1\n2. Accepted the terms of use at https://huggingface.co/pyannote/segmentation-3.1\n3. Accepted the terms of use at https://huggingface.co/pyannote/embedding-3.1\n4. Enabled 'Access to public gated repositories' in your Hugging Face token settings"
            raise Exception(error_msg)

    def cleanup(self):
        """Cleanup function to be called when the service is destroyed."""
        try:
            logger.info("Cleaning up resources...")
            # Force garbage collection
            gc.collect()
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
            # Clear model references
            self.whisper_model = None
            self.diarization_pipeline = None
            
            # Reset initialization flag
            TranscriptionService._initialized = False
            TranscriptionService._instance = None
            
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def perform_diarization(self, audio_path, min_speakers=1, max_speakers=2):
        """Perform speaker diarization on the audio file."""
        try:
            logger.info(f"Starting diarization for {audio_path}")
            
            # Load audio file
            waveform, sample_rate = torchaudio.load(audio_path)
            
            # Convert to mono if stereo
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Resample to 16kHz if necessary (required by the model)
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                waveform = resampler(waveform)
                sample_rate = 16000
            
            logger.info("Running diarization pipeline...")
            diarization = self.diarization_pipeline(
                {"waveform": waveform, "sample_rate": sample_rate},
                min_speakers=min_speakers,
                max_speakers=max_speakers,
                min_duration_on=0.5,
                min_duration_off=0.5
            )
            logger.info("Diarization completed successfully")
            return diarization
                    
        except Exception as e:
            error_msg = f"Error in diarization: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def transcribe_audio(self, audio_path, transcription_id, language=None):
        """Transcribe audio file with speaker diarization."""
        transcription = None
        try:
            logger.info(f"Starting transcription for {audio_path}")
            transcription = Transcription.objects.get(id=transcription_id)
            transcription.status = 'processing'
            transcription.save()

            # Get audio duration and load audio
            waveform, sample_rate = torchaudio.load(audio_path)
            duration = waveform.shape[1] / sample_rate
            transcription.duration = duration

            # Perform diarization
            diarization = self.perform_diarization(audio_path)
            
            # Get number of speakers
            speakers = set()
            for _, _, speaker in diarization.itertracks(yield_label=True):
                speakers.add(speaker)
            transcription.num_speakers = len(speakers)
            transcription.save()

            # Process each segment
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                # Extract audio segment
                start_sample = int(turn.start * sample_rate)
                end_sample = int(turn.end * sample_rate)
                segment_audio = waveform[:, start_sample:end_sample]
                
                # Save segment to temporary file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_path = temp_file.name
                    torchaudio.save(temp_path, segment_audio, sample_rate)
                
                try:
                    # Transcribe segment using Whisper
                    result = self.whisper_model.transcribe(
                        temp_path,
                        language=language,  # Use provided language or auto-detect
                        task="transcribe"
                    )
                    text = result["text"].strip()
                    confidence = result.get("confidence", 0.0)
                    detected_language = result.get("language", language or "en")
                    
                    # Create transcription segment
                    TranscriptionSegment.objects.create(
                        transcription=transcription,
                        start_time=turn.start,
                        end_time=turn.end,
                        text=text,
                        confidence=confidence,
                        speaker=f"SPEAKER_{speaker.split('_')[-1]}",
                        language=detected_language
                    )
                    
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

            transcription.status = 'completed'
            transcription.save()
            logger.info(f"Transcription completed successfully for {audio_path}")
            return transcription

        except Exception as e:
            error_msg = f"Error in transcription: {str(e)}"
            logger.error(error_msg)
            if transcription:
                transcription.status = 'failed'
                transcription.error_message = error_msg
                transcription.save()
            raise Exception(error_msg)

    def get_transcription_text(self, transcription_id, format='text'):
        """Get formatted transcription text with speaker information.
        
        Args:
            transcription_id: ID of the transcription
            format: Output format ('text' or 'json')
        """
        try:
            transcription = Transcription.objects.get(id=transcription_id)
            segments = TranscriptionSegment.objects.filter(
                transcription=transcription
            ).order_by('start_time')

            if format == 'json':
                # Return structured JSON format
                return {
                    'id': transcription.id,
                    'status': transcription.status,
                    'duration': transcription.duration,
                    'num_speakers': transcription.num_speakers,
                    'language': transcription.language,
                    'segments': [
                        {
                            'speaker': segment.speaker,
                            'start_time': segment.start_time,
                            'end_time': segment.end_time,
                            'text': segment.text,
                            'confidence': segment.confidence,
                            'language': segment.language
                        }
                        for segment in segments
                    ]
                }
            else:
                # Return formatted text
                formatted_text = []
                for segment in segments:
                    timestamp = f"[{segment.start_time:.2f}-{segment.end_time:.2f}]"
                    speaker = segment.speaker
                    text = segment.text
                    formatted_text.append(f"{timestamp} {speaker}: {text}")

                return "\n".join(formatted_text)

        except Exception as e:
            error_msg = f"Error getting transcription text: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) 