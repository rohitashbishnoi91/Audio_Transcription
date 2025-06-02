import os
import requests
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_token():
    # Load environment variables
    load_dotenv()
    
    # Get token
    token = os.getenv('PYANNOTE_AUTH_TOKEN')
    if not token:
        logger.error("No token found in environment variables")
        return
    
    logger.info(f"Token length: {len(token)}")
    logger.info(f"Token starts with: {token[:4]}...")
    logger.info(f"Token ends with: ...{token[-4:]}")
    
    # Test token with Hugging Face API
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Check user info
    logger.info("\nTesting user info endpoint...")
    try:
        response = requests.get(
            "https://huggingface.co/api/whoami",
            headers=headers,
            timeout=10
        )
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    
    # Test 2: Check model access
    models = [
        "pyannote/speaker-diarization-3.1",
        "pyannote/segmentation-3.1",
        "pyannote/embedding-3.1"
    ]
    
    for model in models:
        logger.info(f"\nTesting access to {model}...")
        try:
            response = requests.get(
                f"https://huggingface.co/api/models/{model}",
                headers=headers,
                timeout=10
            )
            logger.info(f"Status code: {response.status_code}")
            logger.info(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    test_token() 