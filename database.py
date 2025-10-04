"""Database models and operations for Friends League tracker."""

import errno
import sqlite3
import json
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from config import settings

try:
    import psycopg
except ImportError:  # pragma: no cover - optional when using SQLite fallback
    psycopg = None


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
    """Manages database operations."""
    
    def __init__(self, db_path: str = None, db_url: str = None):
        self.db_url = (db_url or settings.database_url) or ""
        self.use_postgres = bool(self.db_url)
        
        if self.use_postgres:
            if psycopg is None:
                raise RuntimeError("psycopg is required when DATABASE_URL is set")
            self.db_url = self._apply_ssl_mode(self.db_url)
            self._init_postgres()
        else:
            self.db_path = Path(db_path or settings.database_path)
            self._ensure_database_directory()
            self._init_sqlite()
    
    def _ensure_database_directory(self):
        """Ensure the database directory exists."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            if exc.errno != errno.EROFS:
                raise
            fallback_dir = Path("/tmp/data")
            fallback_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = fallback_dir / self.db_path.name
    
    def _apply_ssl_mode(self, url: str) -> str:
        """Ensure SSL mode is enforced on the connection string."""
        if "sslmode=" in url.lower():
            return url
        parsed = urlparse(url)
        query = dict(parse_qsl(parsed.query))
        query["sslmode"] = settings.database_ssl_mode
        new_query = urlencode(query)
        return urlunparse(parsed._replace(query=new_query))

    def _init_sqlite(self):
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

            # Settings table for configuration
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    def _init_postgres(self):
        """Initialize tables for Postgres."""
        ddl_statements = [
            """
            CREATE TABLE IF NOT EXISTS players (
                tag TEXT PRIMARY KEY,
                name TEXT,
                trophies INTEGER,
                last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS battles (
                match_id TEXT PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                player1 TEXT NOT NULL,
                player2 TEXT NOT NULL,
                winner TEXT NOT NULL,
                loser TEXT NOT NULL,
                crowns INTEGER NOT NULL,
                battle_type TEXT NOT NULL,
                deck1 TEXT,
                deck2 TEXT,
                elo_change_winner DOUBLE PRECISION,
                elo_change_loser DOUBLE PRECISION,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player1) REFERENCES players (tag),
                FOREIGN KEY (player2) REFERENCES players (tag)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS player_stats (
                player_tag TEXT PRIMARY KEY,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                total_crowns INTEGER DEFAULT 0,
                elo_rating DOUBLE PRECISION DEFAULT 1200.0,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_tag) REFERENCES players (tag)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]

        with self._connect_postgres() as conn:
            with conn.cursor() as cursor:
                for stmt in ddl_statements:
                    cursor.execute(stmt)
            conn.commit()

    def _connect_postgres(self):
        return psycopg.connect(self.db_url)
    
    def add_player(self, tag: str, name: str = None, trophies: int = None):
        """Add or update a player."""
        if self.use_postgres:
            with self._connect_postgres() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO players (tag, name, trophies, last_updated)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (tag)
                        DO UPDATE SET name = EXCLUDED.name,
                                      trophies = EXCLUDED.trophies,
                                      last_updated = CURRENT_TIMESTAMP
                        """,
                        (tag, name, trophies)
                    )
                conn.commit()
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO players (tag, name, trophies, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (tag, name, trophies))
            conn.commit()
    
    def add_battle(self, battle: Battle) -> bool:
        """Add a battle if it doesn't already exist."""
        if self.use_postgres:
            with self._connect_postgres() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1 FROM battles WHERE match_id = %s", (battle.match_id,))
                    if cursor.fetchone():
                        return False

                    cursor.execute(
                        """
                        INSERT INTO battles (
                            match_id, timestamp, player1, player2, winner, loser,
                            crowns, battle_type, deck1, deck2, elo_change_winner, elo_change_loser
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
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
                            battle.elo_change_loser,
                        )
                    )
                conn.commit()
            return True

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
        query = (
            "SELECT match_id, timestamp, player1, player2, winner, loser, crowns, "
            "battle_type, deck1, deck2, elo_change_winner, elo_change_loser "
            "FROM battles {where_clause} ORDER BY timestamp DESC LIMIT {limit_placeholder}"
        )

        season_start = self.get_season_start_date()

        if self.use_postgres:
            with self._connect_postgres() as conn:
                with conn.cursor() as cursor:
                    if season_start:
                        cursor.execute(
                            query.format(where_clause="WHERE DATE(timestamp) >= %s", limit_placeholder="%s"),
                            (season_start, limit),
                        )
                    else:
                        cursor.execute(
                            query.format(where_clause="WHERE timestamp >= NOW() - INTERVAL '1 day'", limit_placeholder="%s"),
                            (limit,),
                        )
                    rows = cursor.fetchall()
            
            return [
                Battle(
                    match_id=row[0],
                    timestamp=row[1] if isinstance(row[1], datetime) else datetime.fromisoformat(str(row[1])),
                    player1=row[2],
                    player2=row[3],
                    winner=row[4],
                    loser=row[5],
                    crowns=row[6],
                    battle_type=row[7],
                    deck1=json.loads(row[8]) if row[8] else None,
                    deck2=json.loads(row[9]) if row[9] else None,
                    elo_change_winner=row[10],
                    elo_change_loser=row[11],
                )
                for row in rows
            ]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if season_start:
                cursor.execute(
                    """
                    SELECT match_id, timestamp, player1, player2, winner, loser,
                           crowns, battle_type, deck1, deck2, elo_change_winner, elo_change_loser
                    FROM battles
                    WHERE DATE(timestamp) >= DATE(?)
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (season_start.isoformat(), limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT match_id, timestamp, player1, player2, winner, loser,
                           crowns, battle_type, deck1, deck2, elo_change_winner, elo_change_loser
                    FROM battles
                    WHERE DATE(timestamp) >= DATE('now', '-1 day')
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            battles = []
            for row in cursor.fetchall():
                battles.append(
                    Battle(
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
                        elo_change_loser=row[11],
                    )
                )
            return battles
    
    def get_player_stats(self, player_tag: str) -> Optional[Dict[str, Any]]:
        """Get player statistics."""
        if self.use_postgres:
            with self._connect_postgres() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT wins, losses, total_crowns, elo_rating, current_streak, longest_streak
                        FROM player_stats
                        WHERE player_tag = %s
                        """,
                        (player_tag,),
                    )
                    row = cursor.fetchone()

            if not row:
                return None

            wins, losses, total_crowns, elo_rating, current_streak, longest_streak = row
            total_games = wins + losses
            winrate = wins / total_games * 100 if total_games > 0 else 0

            return {
                "wins": wins,
                "losses": losses,
                "total_crowns": total_crowns,
                "elo_rating": elo_rating,
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "winrate": winrate,
            }

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
        if self.use_postgres:
            with self._connect_postgres() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO player_stats (
                            player_tag, wins, losses, total_crowns, elo_rating,
                            current_streak, longest_streak, last_updated
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (player_tag) DO UPDATE SET
                            wins = EXCLUDED.wins,
                            losses = EXCLUDED.losses,
                            total_crowns = EXCLUDED.total_crowns,
                            elo_rating = EXCLUDED.elo_rating,
                            current_streak = EXCLUDED.current_streak,
                            longest_streak = EXCLUDED.longest_streak,
                            last_updated = CURRENT_TIMESTAMP
                        """,
                        (
                            player_tag,
                            stats.get("wins", 0),
                            stats.get("losses", 0),
                            stats.get("total_crowns", 0),
                            stats.get("elo_rating", 1200.0),
                            stats.get("current_streak", 0),
                            stats.get("longest_streak", 0),
                        ),
                    )
                conn.commit()
            return

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
        if self.use_postgres:
            with self._connect_postgres() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE battles
                        SET elo_change_winner = %s,
                            elo_change_loser = %s
                        WHERE match_id = %s
                        """,
                        (elo_change_winner, elo_change_loser, match_id),
                    )
                conn.commit()
            return

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
        if self.use_postgres:
            with self._connect_postgres() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT ps.player_tag, p.name, ps.wins, ps.losses, ps.total_crowns,
                               ps.elo_rating, ps.current_streak, ps.longest_streak
                        FROM player_stats ps
                        LEFT JOIN players p ON ps.player_tag = p.tag
                        ORDER BY ps.elo_rating DESC, ps.wins DESC
                        """
                    )
                    rows = cursor.fetchall()

            stats: List[Dict[str, Any]] = []
            for row in rows:
                wins, losses = row[2], row[3]
                total_games = wins + losses
                winrate = wins / total_games * 100 if total_games > 0 else 0
                stats.append(
                    {
                        "player_tag": row[0],
                        "name": row[1],
                        "wins": wins,
                        "losses": losses,
                        "total_crowns": row[4],
                        "elo_rating": row[5],
                        "current_streak": row[6],
                        "longest_streak": row[7],
                        "winrate": winrate,
                    }
                )
            return stats

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

    def get_season_start_date(self) -> Optional[date]:
        """Get the configured season start date."""
        if self.use_postgres:
            with self._connect_postgres() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT value FROM settings WHERE key = %s", ("season_start_date",))
                    row = cursor.fetchone()
            if row and row[0]:
                try:
                    return datetime.fromisoformat(row[0]).date()
                except ValueError:
                    return None
            return None

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", ("season_start_date",))
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    return datetime.fromisoformat(row[0]).date()
                except ValueError:
                    return None
            return None

    def set_season_start_date(self, value: date | datetime) -> None:
        """Persist the season start date."""
        if isinstance(value, datetime):
            date_str = value.date().isoformat()
        else:
            date_str = value.isoformat()

        if self.use_postgres:
            with self._connect_postgres() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO settings (key, value, updated_at)
                        VALUES ('season_start_date', %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
                        """,
                        (date_str,),
                    )
                conn.commit()
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES ('season_start_date', ?, CURRENT_TIMESTAMP)
                """,
                (date_str,)
            )
            conn.commit()


# Global database manager instance
db_manager = DatabaseManager()
