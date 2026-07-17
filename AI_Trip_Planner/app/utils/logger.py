import logging
import sys

# Configure logger format
logging_format = "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=logging_format,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
