"""Vercel API route for leaderboard data."""

import os
import sys
import json
import logging
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db_manager
from config import settings
from ranking_system import stats_calculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handler(request):
    """Vercel serverless function handler for leaderboard."""
    try:
        # Refresh stats to ensure we only include battles since season start
        player_tags = settings.get_player_tags_list()
        if player_tags:
            stats_calculator.update_all_player_stats(player_tags)

        # Get all player stats
        all_stats = db_manager.get_all_player_stats()
        
        # Get total matches count
        recent_battles = db_manager.get_recent_battles(limit=1000)
        total_matches = len(recent_battles)
        
        # Convert to response format
        players = []
        for stats in all_stats:
            players.append({
                "player_tag": stats['player_tag'],
                "name": stats['name'],
                "wins": stats['wins'],
                "losses": stats['losses'],
                "total_crowns": stats['total_crowns'],
                "elo_rating": stats['elo_rating'],
                "current_streak": stats['current_streak'],
                "longest_streak": stats['longest_streak'],
                "winrate": stats['winrate']
            })
        
        response_data = {
            "players": players,
            "last_updated": recent_battles[0].timestamp.isoformat() if recent_battles else "",
            "total_matches": total_matches
        }
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps(response_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": "Internal server error"})
        }
