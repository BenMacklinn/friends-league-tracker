"""Vercel API route for recent battles."""

import os
import sys
import json
import logging
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import db_manager
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handler(request):
    """Vercel serverless function handler for recent battles."""
    try:
        # Get limit from query parameters
        limit = 50
        if 'queryStringParameters' in request and request['queryStringParameters']:
            limit_param = request['queryStringParameters'].get('limit')
            if limit_param:
                try:
                    limit = int(limit_param)
                except ValueError:
                    limit = 50
        
        battles = db_manager.get_recent_battles(limit=limit)
        
        battle_info = []
        for battle in battles:
            logger.info(f"Battle ELO changes: winner={battle.elo_change_winner}, loser={battle.elo_change_loser}")
            battle_info.append({
                "match_id": battle.match_id,
                "timestamp": battle.timestamp.isoformat(),
                "player1": battle.player1,
                "player2": battle.player2,
                "winner": battle.winner,
                "loser": battle.loser,
                "crowns": battle.crowns,
                "battle_type": battle.battle_type,
                "elo_change_winner": battle.elo_change_winner,
                "elo_change_loser": battle.elo_change_loser
            })
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps(battle_info)
        }
        
    except Exception as e:
        logger.error(f"Error getting recent battles: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": "Internal server error"})
        }
