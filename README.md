# Audio Transcription and Blog Title Generation System

A Django-based application that provides audio transcription with speaker diarization and template-based blog title generation.

## Features

### 1. Audio Transcription with Diarization
- Transcribes audio files using OpenAI's Whisper model
- Performs speaker diarization using Pyannote.audio
- Supports multiple languages
- Returns results in both text and JSON formats
- Includes speaker identification ("who spoke when")
- Handles various audio formats (WAV, MP3, etc.)

### 2. Blog Title Generation
- Generates title suggestions using a template-based approach
- Provides diverse title suggestions based on content analysis
- Includes confidence scores for suggestions
- Supports title updates and regeneration
- Uses a simple but effective pattern matching system
- Templates include various formats like:
  * "The Future of {topic}"
  * "Understanding {topic}: A Comprehensive Guide"
  * "How {topic} is Changing the World"
  * "The Impact of {topic} on Society"
  * "Exploring the World of {topic}"
  * "Why {topic} Matters in 2024"
  * "The Evolution of {topic}"
  * "Breaking Down {topic}: What You Need to Know"

## Prerequisites

- Python 3.8 or higher
- CUDA-capable GPU (optional, but recommended)
- Hugging Face account with access token

## Installation

1. Clone the repository:
```bash
git clone https://github.com/rohitashbishnoi91/Audio_Transcription.git
cd Audio_Transcription
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix/MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```
PYANNOTE_AUTH_TOKEN=your_huggingface_token_here
```

5. Accept the terms of use for the required models:
   - Visit https://huggingface.co/pyannote/speaker-diarization-3.1
   - Visit https://huggingface.co/pyannote/segmentation-3.1
   - Visit https://huggingface.co/pyannote/embedding-3.1
   - Enable "Access to public gated repositories" in your Hugging Face token settings

6. Run migrations:
```bash
python manage.py migrate
```

7. Start the development server:
```bash
python manage.py runserver
```

## API Endpoints

### Audio Transcription

1. Create Transcription:
```http
POST /api/transcriptions/
Content-Type: multipart/form-data

Parameters:
- audio_file: Audio file (WAV, MP3, etc.)
- language: Optional language code (e.g., 'en', 'es', 'fr')

Response:
{
    "id": "transcription_id",
    "status": "processing",
    "duration": 120.5,
    "num_speakers": 2,
    "segments": [
        {
            "speaker": "SPEAKER_1",
            "start_time": 0.0,
            "end_time": 5.2,
            "text": "Transcribed text here",
            "confidence": 0.95,
            "language": "en"
        }
    ]
}
```

2. Check Status:
```http
GET /api/transcriptions/{id}/status/

Response:
{
    "id": "transcription_id",
    "status": "completed",
    "duration": 120.5,
    "num_speakers": 2,
    "language": "en",
    "error_message": null
}
```

3. Get Transcription:
```http
GET /api/transcriptions/{id}/text/?format=json

Response:
{
    "id": "transcription_id",
    "status": "completed",
    "duration": 120.5,
    "num_speakers": 2,
    "language": "en",
    "segments": [
        {
            "speaker": "SPEAKER_1",
            "start_time": 0.0,
            "end_time": 5.2,
            "text": "Transcribed text here",
            "confidence": 0.95,
            "language": "en"
        }
    ]
}
```

### Blog Title Generation

1. Create Blog Post with Title Suggestions:
```http
POST /api/blog-posts/
Content-Type: application/json

{
    "content": "Your blog post content here..."
}

Response:
{
    "id": "blog_post_id",
    "title": "Generated Title",
    "title_suggestions": [
        "Title Suggestion 1",
        "Title Suggestion 2",
        "Title Suggestion 3"
    ],
    "status": "draft",
    "created_at": "2024-03-14T12:00:00Z"
}
```

2. Generate New Title Suggestions:
```http
POST /api/blog-posts/{id}/generate_titles/
Content-Type: application/json

{
    "num_titles": 3  // optional, defaults to 3
}

Response:
{
    "blog_post_id": "blog_post_id",
    "current_title": "Current Title",
    "title_suggestions": [
        "New Title Suggestion 1",
        "New Title Suggestion 2",
        "New Title Suggestion 3"
    ]
}
```

3. Update Blog Post Title:
```http
POST /api/blog-posts/{id}/update_title/
Content-Type: application/json

{
    "title": "New Title"
}

Response:
{
    "id": "blog_post_id",
    "title": "New Title",
    "status": "draft",
    "updated_at": "2024-03-14T12:30:00Z"
}
```

## Project Structure

```
Audio_Transcription/
├── audio_blog_project/     # Django project settings
│   ├── models.py          # Blog post models
│   ├── services.py        # Title generation service
│   ├── views.py           # API views
│   └── serializers.py     # Data serializers
├── transcription/         # Transcription application
│   ├── models.py          # Transcription models
│   ├── services.py        # Transcription service
│   ├── views.py           # API views
│   └── serializers.py     # Data serializers
├── model_cache/           # Cached AI models
├── manage.py              # Django management script
├── requirements.txt       # Project dependencies
└── .env                   # Environment variables
```

## Technical Details

### Models Used
- **Transcription**: Whisper (OpenAI) for speech recognition
- **Diarization**: Pyannote.audio for speaker identification
- **Title Generation**: Template-based system with pattern matching

### Features
- GPU acceleration when available
- Model caching for better performance
- Template-based title generation with multiple patterns
- Comprehensive error handling
- Status tracking for long operations
- Multilingual support
- RESTful API design

### Error Handling
- Input validation
- File size and type checking
- Model initialization errors
- Token verification
- API error responses

## Testing

To test the endpoints, you can use tools like Postman or curl. Example curl commands:

1. Create transcription:
```bash
curl -X POST -F "audio_file=@audio.wav" http://localhost:8000/api/transcriptions/
```

2. Create blog post:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"content":"Your blog post content"}' http://localhost:8000/api/blog-posts/
```

## Notes

- The first run will download the required models, which may take some time
- GPU is recommended for better performance
- Ensure your Hugging Face token has the correct permissions
- Accept the terms of use for all required models
- The system supports various audio formats but works best with WAV files
- Title generation uses a template-based approach for reliable and consistent results

## Author

Rohitash Bishnoi 
