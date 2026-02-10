from modules.YA_Secrets.secrets_parser import load_secrets, get_secret
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("hello_secrets")

if __name__ == "__main__":
    logger.info(f"All secrets: {load_secrets()}")
    logger.info(f"API KEY = {get_secret('api_key')}")
