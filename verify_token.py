import os
import requests
from dotenv import load_dotenv
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_token():
    # Load environment variables
    load_dotenv()
    
    # Get token
    token = os.getenv('PYANNOTE_AUTH_TOKEN')
    if not token:
        logger.error("No PYANNOTE_AUTH_TOKEN found in environment variables")
        return
    
    # Remove any whitespace from token
    token = token.strip()
    
    logger.info(f"Token length: {len(token)}")
    logger.info(f"Token format: {token[:4]}...{token[-4:]}")
    logger.info(f"Token contains spaces: {' ' in token}")
    logger.info(f"Token contains newlines: {'\n' in token}")
    
    # Test token with Hugging Face API
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Print the exact header being sent (masking the token)
    masked_token = f"{token[:4]}...{token[-4:]}"
    logger.info(f"\nRequest headers:")
    logger.info(f"Authorization: Bearer {masked_token}")
    
    # Test 1: Check user info
    logger.info("\n1. Testing user authentication...")
    try:
        response = requests.get(
            "https://huggingface.co/api/whoami",
            headers=headers,
            timeout=10
        )
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        if response.status_code == 200:
            user_info = response.json()
            logger.info(f"Authenticated as: {user_info.get('name', 'Unknown')}")
            logger.info(f"Email: {user_info.get('email', 'Not provided')}")
        else:
            logger.error(f"Authentication failed: {response.text}")
            # Try to parse the error response
            try:
                error_info = response.json()
                logger.error(f"Error details: {json.dumps(error_info, indent=2)}")
            except:
                logger.error(f"Raw response: {response.text}")
            return
    except Exception as e:
        logger.error(f"Error checking authentication: {str(e)}")
        return
    
    # Test 2: Check model access and terms of use
    models = [
        "pyannote/speaker-diarization-3.1",
        "pyannote/segmentation-3.1",
        "pyannote/embedding-3.1"
    ]
    
    logger.info("\n2. Checking model access and terms of use...")
    for model in models:
        logger.info(f"\nChecking {model}...")
        try:
            # Check model access
            response = requests.get(
                f"https://huggingface.co/api/models/{model}",
                headers=headers,
                timeout=10
            )
            logger.info(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                model_info = response.json()
                logger.info("✓ Model access verified")
                
                # Check if terms of use are accepted
                terms_url = f"https://huggingface.co/api/models/{model}/terms"
                terms_response = requests.get(terms_url, headers=headers, timeout=10)
                if terms_response.status_code == 200:
                    terms_info = terms_response.json()
                    if terms_info.get('accepted', False):
                        logger.info("✓ Terms of use accepted")
                    else:
                        logger.warning("⚠ Terms of use not accepted")
                        logger.info(f"Please visit: https://huggingface.co/{model} to accept terms")
                else:
                    logger.warning(f"⚠ Could not verify terms of use: {terms_response.text}")
            else:
                logger.error(f"✗ Model access failed: {response.text}")
                if response.status_code == 401:
                    logger.info("This might be because:")
                    logger.info("1. Token doesn't have 'Access to public gated repositories' enabled")
                    logger.info("2. Terms of use haven't been accepted")
                    logger.info(f"Please visit: https://huggingface.co/{model}")
        except Exception as e:
            logger.error(f"Error checking model {model}: {str(e)}")

if __name__ == "__main__":
    verify_token() 