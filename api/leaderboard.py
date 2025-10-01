"""Vercel API route for leaderboard data."""

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db_manager
from ranking_system import stats_calculator
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Friends League Tracker API",
    description="Clash Royale Friends League leaderboard and statistics",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlayerStats(BaseModel):
    """Player statistics model."""
    player_tag: str
    name: Optional[str] = None
    wins: int
    losses: int
    total_crowns: int
    elo_rating: float
    current_streak: int
    longest_streak: int
    winrate: float


class LeaderboardResponse(BaseModel):
    """Leaderboard response model."""
    players: List[PlayerStats]
    last_updated: str
    total_matches: int


@app.get("/", response_model=LeaderboardResponse)
async def get_leaderboard():
    """Get the current leaderboard."""
    try:
        # Get all player stats
        all_stats = db_manager.get_all_player_stats()
        
        # Get total matches count
        recent_battles = db_manager.get_recent_battles(limit=1000)
        total_matches = len(recent_battles)
        
        # Convert to response model
        players = []
        for stats in all_stats:
            players.append(PlayerStats(
                player_tag=stats['player_tag'],
                name=stats['name'],
                wins=stats['wins'],
                losses=stats['losses'],
                total_crowns=stats['total_crowns'],
                elo_rating=stats['elo_rating'],
                current_streak=stats['current_streak'],
                longest_streak=stats['longest_streak'],
                winrate=stats['winrate']
            ))
        
        return LeaderboardResponse(
            players=players,
            last_updated=recent_battles[0].timestamp.isoformat() if recent_battles else "",
            total_matches=total_matches
        )
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Vercel handler
def handler(request):
    """Vercel serverless function handler."""
    return app
