import os
from pathlib import Path
from dotenv import load_dotenv, dotenv_values
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_token():
    # Get current directory
    current_dir = Path.cwd()
    env_path = current_dir / '.env'
    
    # Read token directly from .env file
    if env_path.exists():
        env_values = dotenv_values(env_path)
        env_token = env_values.get('PYANNOTE_AUTH_TOKEN', '')
        logger.info("Token from .env file:")
        logger.info(f"Length: {len(env_token)}")
        logger.info(f"Starts with: {env_token[:4]}...")
        logger.info(f"Ends with: ...{env_token[-4:]}")
    else:
        logger.error(".env file not found!")
    
    # Get token from environment
    env_var_token = os.getenv('PYANNOTE_AUTH_TOKEN', '')
    logger.info("\nToken from environment variable:")
    logger.info(f"Length: {len(env_var_token)}")
    logger.info(f"Starts with: {env_var_token[:4] if env_var_token else 'None'}...")
    logger.info(f"Ends with: ...{env_var_token[-4:] if env_var_token else 'None'}")
    
    # Compare tokens
    if env_token and env_var_token:
        if env_token == env_var_token:
            logger.info("\n✓ Tokens match!")
        else:
            logger.error("\n✗ Tokens do not match!")
            logger.info("This means the environment variable is not being updated from the .env file")
    else:
        logger.warning("\n⚠ Could not compare tokens - one or both are empty")

if __name__ == "__main__":
    check_token() 