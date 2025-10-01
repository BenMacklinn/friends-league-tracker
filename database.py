"""Database models and operations for Friends League tracker."""

import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from config import settings


@dataclass
class Battle:
    """Represents a battle between two players."""
    match_id: str
    timestamp: datetime
    player1: str
    player2: str
    winner: str
    loser: str
    crowns: int
    battle_type: str
    deck1: Optional[Dict[str, Any]] = None
    deck2: Optional[Dict[str, Any]] = None
    elo_change_winner: Optional[float] = None
    elo_change_loser: Optional[float] = None


class DatabaseManager:
    """Manages SQLite database operations."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_path
        self._ensure_database_directory()
        self._init_database()
    
    def _ensure_database_directory(self):
        """Ensure the database directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Players table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    tag TEXT PRIMARY KEY,
                    name TEXT,
                    trophies INTEGER,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Battles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS battles (
                    match_id TEXT PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    player1 TEXT NOT NULL,
                    player2 TEXT NOT NULL,
                    winner TEXT NOT NULL,
                    loser TEXT NOT NULL,
                    crowns INTEGER NOT NULL,
                    battle_type TEXT NOT NULL,
                    deck1 TEXT,
                    deck2 TEXT,
                    elo_change_winner REAL,
                    elo_change_loser REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player1) REFERENCES players (tag),
                    FOREIGN KEY (player2) REFERENCES players (tag)
                )
            """)
            
            # Player stats table (computed from battles)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS player_stats (
                    player_tag TEXT PRIMARY KEY,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    total_crowns INTEGER DEFAULT 0,
                    elo_rating REAL DEFAULT 1200.0,
                    current_streak INTEGER DEFAULT 0,
                    longest_streak INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_tag) REFERENCES players (tag)
                )
            """)
            
            # Add ELO change columns if they don't exist
            try:
                cursor.execute("ALTER TABLE battles ADD COLUMN elo_change_winner REAL")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute("ALTER TABLE battles ADD COLUMN elo_change_loser REAL")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            conn.commit()
    
    def add_player(self, tag: str, name: str = None, trophies: int = None):
        """Add or update a player."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO players (tag, name, trophies, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (tag, name, trophies))
            conn.commit()
    
    def add_battle(self, battle: Battle) -> bool:
        """Add a battle if it doesn't already exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if battle already exists
            cursor.execute("SELECT 1 FROM battles WHERE match_id = ?", (battle.match_id,))
            if cursor.fetchone():
                return False  # Battle already exists
            
            # Insert battle
            cursor.execute("""
                INSERT INTO battles (
                    match_id, timestamp, player1, player2, winner, loser,
                    crowns, battle_type, deck1, deck2, elo_change_winner, elo_change_loser
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                battle.match_id,
                battle.timestamp,
                battle.player1,
                battle.player2,
                battle.winner,
                battle.loser,
                battle.crowns,
                battle.battle_type,
                json.dumps(battle.deck1) if battle.deck1 else None,
                json.dumps(battle.deck2) if battle.deck2 else None,
                battle.elo_change_winner,
                battle.elo_change_loser
            ))
            conn.commit()
            return True
    
    def get_recent_battles(self, limit: int = 100) -> List[Battle]:
        """Get recent battles."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT match_id, timestamp, player1, player2, winner, loser,
                       crowns, battle_type, deck1, deck2, elo_change_winner, elo_change_loser
                FROM battles
                WHERE DATE(timestamp) >= DATE('now', '-1 day')
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            battles = []
            for row in cursor.fetchall():
                battles.append(Battle(
                    match_id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    player1=row[2],
                    player2=row[3],
                    winner=row[4],
                    loser=row[5],
                    crowns=row[6],
                    battle_type=row[7],
                    deck1=json.loads(row[8]) if row[8] else None,
                    deck2=json.loads(row[9]) if row[9] else None,
                    elo_change_winner=row[10],
                    elo_change_loser=row[11]
                ))
            return battles
    
    def get_player_stats(self, player_tag: str) -> Optional[Dict[str, Any]]:
        """Get player statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT wins, losses, total_crowns, elo_rating, current_streak, longest_streak
                FROM player_stats
                WHERE player_tag = ?
            """, (player_tag,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'wins': row[0],
                'losses': row[1],
                'total_crowns': row[2],
                'elo_rating': row[3],
                'current_streak': row[4],
                'longest_streak': row[5],
                'winrate': row[0] / (row[0] + row[1]) * 100 if (row[0] + row[1]) > 0 else 0
            }
    
    def update_player_stats(self, player_tag: str, stats: Dict[str, Any]):
        """Update player statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO player_stats (
                    player_tag, wins, losses, total_crowns, elo_rating,
                    current_streak, longest_streak, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                player_tag,
                stats.get('wins', 0),
                stats.get('losses', 0),
                stats.get('total_crowns', 0),
                stats.get('elo_rating', 1200.0),
                stats.get('current_streak', 0),
                stats.get('longest_streak', 0)
            ))
            conn.commit()
    
    def update_battle_elo_changes(self, match_id: str, elo_change_winner: float, elo_change_loser: float):
        """Update ELO changes for a specific battle."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE battles 
                SET elo_change_winner = ?, elo_change_loser = ?
                WHERE match_id = ?
            """, (elo_change_winner, elo_change_loser, match_id))
            conn.commit()
    
    def get_all_player_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all players."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ps.player_tag, p.name, ps.wins, ps.losses, ps.total_crowns,
                       ps.elo_rating, ps.current_streak, ps.longest_streak
                FROM player_stats ps
                LEFT JOIN players p ON ps.player_tag = p.tag
                ORDER BY ps.elo_rating DESC, ps.wins DESC
            """)
            
            stats = []
            for row in cursor.fetchall():
                wins, losses = row[2], row[3]
                winrate = wins / (wins + losses) * 100 if (wins + losses) > 0 else 0
                
                stats.append({
                    'player_tag': row[0],
                    'name': row[1],
                    'wins': wins,
                    'losses': losses,
                    'total_crowns': row[4],
                    'elo_rating': row[5],
                    'current_streak': row[6],
                    'longest_streak': row[7],
                    'winrate': winrate
                })
            return stats


# Global database manager instance
db_manager = DatabaseManager()
