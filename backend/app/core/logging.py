import logging
import sys
from app.core.config import settings


def setup_logging():
    log_format = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    # Reduce noise from third-party libraries if desired
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


logger = logging.getLogger("securebank")
