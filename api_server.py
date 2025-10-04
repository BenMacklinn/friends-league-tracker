"""FastAPI server for Friends League tracker."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from database import db_manager
from ranking_system import stats_calculator
from config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Friends League Tracker",
    description="Clash Royale Friends League leaderboard and statistics",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint."""
    return {
        "message": "Friends League Tracker API",
        "version": "1.0.0",
        "endpoints": {
            "leaderboard": "/leaderboard",
            "player_stats": "/player/{player_tag}",
            "recent_battles": "/battles/recent",
            "health": "/health"
        }
    }


@app.get("/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "friends-league-tracker"}


@app.get("/leaderboard", response_model=LeaderboardResponse)
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


@app.get("/player/{player_tag}", response_model=PlayerStats)
async def get_player_stats(player_tag: str):
    """Get statistics for a specific player."""
    try:
        # Clean player tag
        clean_tag = player_tag.replace('#', '')
        
        stats = db_manager.get_player_stats(clean_tag)
        if not stats:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Get player name from database
        # This would require a separate query to get player info
        # For now, we'll use the tag as the name
        
        return PlayerStats(
            player_tag=clean_tag,
            name=clean_tag,  # TODO: Get actual name from players table
            wins=stats['wins'],
            losses=stats['losses'],
            total_crowns=stats['total_crowns'],
            elo_rating=stats['elo_rating'],
            current_streak=stats['current_streak'],
            longest_streak=stats['longest_streak'],
            winrate=stats['winrate']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player stats for {player_tag}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/battles/recent", response_model=List[BattleInfo])
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


@app.post("/refresh", response_model=Dict[str, str])
async def refresh_data():
    """Manually trigger data refresh."""
    try:
        # This would trigger the background task to fetch new data
        # For now, just return a success message
        return {"message": "Data refresh triggered", "status": "success"}
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
