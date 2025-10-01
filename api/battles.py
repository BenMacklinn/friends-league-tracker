"""Vercel API route for battle data."""

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
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Friends League Tracker API",
    description="Clash Royale Friends League battle data",
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


class BattleInfo(BaseModel):
    """Battle information model."""
    match_id: str
    timestamp: str
    player1: str
    player2: str
    winner: str
    loser: str
    crowns: int
    battle_type: str
    elo_change_winner: Optional[float] = None
    elo_change_loser: Optional[float] = None


@app.get("/recent", response_model=List[BattleInfo])
async def get_recent_battles(limit: int = 50):
    """Get recent battles."""
    try:
        battles = db_manager.get_recent_battles(limit=limit)
        
        battle_info = []
        for battle in battles:
            logger.info(f"Battle ELO changes: winner={battle.elo_change_winner}, loser={battle.elo_change_loser}")
            battle_info.append(BattleInfo(
                match_id=battle.match_id,
                timestamp=battle.timestamp.isoformat(),
                player1=battle.player1,
                player2=battle.player2,
                winner=battle.winner,
                loser=battle.loser,
                crowns=battle.crowns,
                battle_type=battle.battle_type,
                elo_change_winner=battle.elo_change_winner,
                elo_change_loser=battle.elo_change_loser
            ))
        
        return battle_info
    except Exception as e:
        logger.error(f"Error getting recent battles: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Vercel handler
def handler(request):
    """Vercel serverless function handler."""
    return app
