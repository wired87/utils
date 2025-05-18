

import logging
import os

LOG_LEVEL = os.environ.get('DJANGO_LOG_LEVEL', 'INFO').upper()

logging.basicConfig(
    level=LOG_LEVEL, # Setzen Sie die gewünschte Log-Stufe
    format='%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - %(message)s', # Format mit Thread-Name
    # format='%(asctime)s - %(name)s - %(levelname)s - %(thread)d - %(message)s', # Alternative: Thread-ID
    handlers=[
        logging.StreamHandler() # Sendet Log-Nachrichten an sys.stderr (Ihre Konsole)
        # Sie können hier auch FileHandler hinzufügen, um in eine Datei zu loggen
    ]
)
LOGGER = logging.getLogger(__name__)



