import logging
import os

LOG_LEVEL = os.environ.get('DJANGO_LOG_LEVEL', 'INFO').upper()

logging.basicConfig(
    level=LOG_LEVEL, # Setzen Sie die gewünschte Log-Stufe
    format='%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - %(message)s', # Format mit Thread-Name
    handlers=[
        logging.StreamHandler()
    ]
)
LOGGER = logging.getLogger(__name__)



