"""Vercel API route for manual data collection."""

import os
import sys
import json
import logging
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from background_scheduler import collect_data
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handler(request):
    """Vercel API handler for manual data collection."""
    try:
        logger.info(f"Starting manual data collection at {datetime.now()}")
        
        # Check if we have the required configuration
        if not settings.clash_royale_api_token:
            logger.error("CLASH_ROYALE_API_TOKEN not configured")
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "API token not configured",
                    "timestamp": datetime.now().isoformat()
                })
            }
        
        if not settings.get_player_tags_list():
            logger.error("No player tags configured")
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "No player tags configured",
                    "timestamp": datetime.now().isoformat()
                })
            }
        
        # Run data collection
        result = collect_data()
        
        if result:
            logger.info("Data collection completed successfully")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Data collection completed successfully",
                    "timestamp": datetime.now().isoformat(),
                    "proxy_enabled": settings.use_royaleapi_proxy
                })
            }
        else:
            logger.error("Data collection failed")
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "Data collection failed",
                    "timestamp": datetime.now().isoformat()
                })
            }
            
    except Exception as e:
        logger.error(f"Error in data collection: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        }
