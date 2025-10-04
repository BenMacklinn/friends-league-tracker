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
        player_tags = settings.get_player_tags_list()
        if not player_tags:
            return LeaderboardResponse(players=[], last_updated="", total_matches=0)

        # Use existing player data only to retrieve names
        existing_stats = {
            item['player_tag']: item.get('name')
            for item in db_manager.get_all_player_stats()
        }

        # Fetch battles since season start once for metadata
        recent_battles = db_manager.get_recent_battles(limit=1000)
        total_matches = len(recent_battles)
        last_updated = recent_battles[0].timestamp.isoformat() if recent_battles else ""

        computed_stats = []
        for tag in player_tags:
            stats = stats_calculator.calculate_player_stats(tag)
            computed_stats.append({
                'player_tag': tag,
                'name': existing_stats.get(tag, tag),
                'wins': stats['wins'],
                'losses': stats['losses'],
                'total_crowns': stats['total_crowns'],
                'elo_rating': stats['elo_rating'],
                'current_streak': stats['current_streak'],
                'longest_streak': stats['longest_streak'],
                'winrate': stats['winrate']
            })

        # Sort by ELO desc, then wins desc
        computed_stats.sort(key=lambda s: (-s['elo_rating'], -s['wins']))

        players = [
            PlayerStats(**player_stat)
            for player_stat in computed_stats
        ]

        return LeaderboardResponse(
            players=players,
            last_updated=last_updated,
            total_matches=total_matches
        )
        
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
