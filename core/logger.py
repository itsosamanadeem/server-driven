import logging
import sys
from dotenv import load_dotenv
import os

load_dotenv()
LOG_LEVEL = os.getenv('LOGGING_LEVEL','INFO').upper()

def setup_logger():
    logging.basicConfig(
        level=LOG_LEVEL,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    )
