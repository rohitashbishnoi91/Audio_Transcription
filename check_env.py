import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_env():
    # Get the current directory
    current_dir = Path.cwd()
    logger.info(f"Current directory: {current_dir}")
    
    # Check for .env in current directory
    env_path = current_dir / '.env'
    logger.info(f"Looking for .env in current directory: {env_path}")
    if env_path.exists():
        logger.info("Found .env in current directory")
        load_dotenv(env_path)
        token = os.getenv('PYANNOTE_AUTH_TOKEN')
        logger.info(f"Token from current directory .env: {bool(token)}")
        if token:
            logger.info(f"Token length: {len(token)}")
            logger.info(f"Token starts with: {token[:4]}...")
    
    # Check for .env in parent directory
    parent_env_path = current_dir.parent / '.env'
    logger.info(f"Looking for .env in parent directory: {parent_env_path}")
    if parent_env_path.exists():
        logger.info("Found .env in parent directory")
        load_dotenv(parent_env_path)
        token = os.getenv('PYANNOTE_AUTH_TOKEN')
        logger.info(f"Token from parent directory .env: {bool(token)}")
        if token:
            logger.info(f"Token length: {len(token)}")
            logger.info(f"Token starts with: {token[:4]}...")
    
    # Check for .env in Django settings directory
    django_env_path = current_dir / 'audio_blog_project' / '.env'
    logger.info(f"Looking for .env in Django settings directory: {django_env_path}")
    if django_env_path.exists():
        logger.info("Found .env in Django settings directory")
        load_dotenv(django_env_path)
        token = os.getenv('PYANNOTE_AUTH_TOKEN')
        logger.info(f"Token from Django settings .env: {bool(token)}")
        if token:
            logger.info(f"Token length: {len(token)}")
            logger.info(f"Token starts with: {token[:4]}...")

if __name__ == "__main__":
    check_env() 