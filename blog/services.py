from django.conf import settings
from .models import BlogPost, TitleSuggestion
import logging
import time
import random
import os
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import tempfile
import shutil
from huggingface_hub import snapshot_download, HfFolder

logger = logging.getLogger(__name__)

class TitleSuggestionService:
    def __init__(self):
        logger.info("Initializing TitleSuggestionService")
        # We'll use a simple mock service for now
        self.is_mock = True
        logger.info("Using mock title generation service")

    def generate_titles(self, content, blog_post=None):
        logger.info("Starting title generation")
        start_time = time.time()
        
        try:
            # Generate mock titles for testing
            base_titles = [
                "The Future of {topic}",
                "Understanding {topic}: A Comprehensive Guide",
                "How {topic} is Changing the World",
                "The Impact of {topic} on Society",
                "Exploring the World of {topic}",
                "Why {topic} Matters in 2024",
                "The Evolution of {topic}",
                "Breaking Down {topic}: What You Need to Know"
            ]
            
            # Extract a topic from the content (simple version)
            words = content.split()
            topic = words[0] if len(words) > 0 else "Technology"
            
            # Generate 3 random titles
            titles = []
            for _ in range(3):
                template = random.choice(base_titles)
                title = template.format(topic=topic)
                titles.append(title)
            
            logger.info(f"Generated mock titles: {titles}")
            
            # If blog_post is provided, save the suggestions
            if blog_post:
                for title in titles:
                    TitleSuggestion.objects.create(
                        blog_post=blog_post,
                        suggested_title=title,
                        confidence_score=0.8
                    )

            end_time = time.time()
            logger.info(f"Title generation completed in {end_time - start_time:.2f} seconds")
            return titles

        except Exception as e:
            end_time = time.time()
            logger.error(f"Error in generate_titles after {end_time - start_time:.2f} seconds: {str(e)}")
            if blog_post:
                TitleSuggestion.objects.create(
                    blog_post=blog_post,
                    suggested_title="Error generating titles",
                    confidence_score=0.0
                )
            return [
                "Error occurred, but here's a test title 1",
                "Error occurred, but here's a test title 2",
                "Error occurred, but here's a test title 3"
            ]

class TitleGenerationService:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TitleGenerationService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if TitleGenerationService._initialized:
            logger.info("TitleGenerationService already initialized, skipping initialization")
            return
            
        try:
            logger.info("Initializing TitleGenerationService...")
            
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
            token = settings.PYANNOTE_AUTH_TOKEN  # Reuse the same token
            if not token:
                raise ValueError("PYANNOTE_AUTH_TOKEN not set in settings")
            
            # Set token in HfFolder for all Hugging Face operations
            HfFolder.save_token(token)
            logger.info("Token verified and set in HfFolder")
            
            # Initialize the title generation model
            logger.info("Initializing title generation model...")
            try:
                # Use a model that's good at summarization and title generation
                model_name = "facebook/bart-large-cnn"
                
                # Download model files
                logger.info(f"Downloading model {model_name}...")
                model_path = snapshot_download(
                    model_name,
                    use_auth_token=token,
                    cache_dir=os.path.join(cache_dir, 'transformers'),
                    local_files_only=False
                )
                
                # Initialize tokenizer and model
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
                
                # Move model to GPU if available
                if torch.cuda.is_available():
                    logger.info("Using GPU for title generation model")
                    self.model = self.model.to(torch.device("cuda"))
                else:
                    logger.info("Using CPU for title generation model")
                
                logger.info("Title generation model initialized successfully")
                
            except Exception as e:
                logger.error(f"Error initializing title generation model: {str(e)}")
                raise
            
            TitleGenerationService._initialized = True
            
        except Exception as e:
            error_msg = f"Error initializing title generation service: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def generate_titles(self, content, num_titles=3, max_length=50):
        """Generate title suggestions for a blog post.
        
        Args:
            content (str): The blog post content
            num_titles (int): Number of title suggestions to generate
            max_length (int): Maximum length of each title
            
        Returns:
            list: List of generated title suggestions
        """
        try:
            logger.info("Generating title suggestions...")
            
            # Prepare the input
            inputs = self.tokenizer(
                content,
                max_length=1024,
                truncation=True,
                return_tensors="pt"
            )
            
            # Move inputs to GPU if available
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            # Generate multiple titles using different sampling strategies
            titles = []
            
            # Strategy 1: Beam search
            outputs = self.model.generate(
                **inputs,
                num_beams=5,
                num_return_sequences=1,
                max_length=max_length,
                early_stopping=True
            )
            title = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            titles.append(title.strip())
            
            # Strategy 2: Top-k sampling
            outputs = self.model.generate(
                **inputs,
                do_sample=True,
                top_k=50,
                num_return_sequences=1,
                max_length=max_length,
                early_stopping=True
            )
            title = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            if title.strip() not in titles:
                titles.append(title.strip())
            
            # Strategy 3: Nucleus sampling
            outputs = self.model.generate(
                **inputs,
                do_sample=True,
                top_p=0.95,
                num_return_sequences=1,
                max_length=max_length,
                early_stopping=True
            )
            title = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            if title.strip() not in titles:
                titles.append(title.strip())
            
            # If we need more titles, use temperature sampling
            while len(titles) < num_titles:
                outputs = self.model.generate(
                    **inputs,
                    do_sample=True,
                    temperature=0.8,
                    num_return_sequences=1,
                    max_length=max_length,
                    early_stopping=True
                )
                title = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                if title.strip() not in titles:
                    titles.append(title.strip())
            
            logger.info(f"Generated {len(titles)} title suggestions")
            return titles[:num_titles]  # Ensure we return exactly num_titles
            
        except Exception as e:
            error_msg = f"Error generating titles: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) 