"""Simplified main entry point."""

import logging
import sys
from src.slack_handler import SlackHandler
from src.config.settings import Config

# Simple logging setup
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def main():
    """Start the K8s troubleshooting agent."""
    try:
        Config.validate()
        handler = SlackHandler()
        logger.info("Starting K8s Troubleshooting Agent...")
        handler.start()
    except ValueError as e:
        logger.error(f"Config error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()