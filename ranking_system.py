"""ELO rating system and statistics calculations."""

import math
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from database import db_manager, Battle

logger = logging.getLogger(__name__)


class ELORatingSystem:
    """ELO rating system for player rankings."""
    
    def __init__(self, initial_rating: float = 1200.0, k_factor: float = 32.0):
        self.initial_rating = initial_rating
        self.k_factor = k_factor
    
    def calculate_expected_score(self, rating_a: float, rating_b: float) -> float:
        """Calculate expected score for player A against player B."""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def update_ratings(self, winner_rating: float, loser_rating: float) -> tuple[float, float, float, float]:
        """Update ELO ratings after a match."""
        expected_winner = self.calculate_expected_score(winner_rating, loser_rating)
        expected_loser = self.calculate_expected_score(loser_rating, winner_rating)
        
        # Winner gets 1 point, loser gets 0
        actual_winner = 1.0
        actual_loser = 0.0
        
        elo_change_winner = self.k_factor * (actual_winner - expected_winner)
        elo_change_loser = self.k_factor * (actual_loser - expected_loser)
        
        new_winner_rating = winner_rating + elo_change_winner
        new_loser_rating = loser_rating + elo_change_loser
        
        return new_winner_rating, new_loser_rating, elo_change_winner, elo_change_loser


class StatisticsCalculator:
    """Calculates player statistics from battle data."""
    
    def __init__(self, elo_system: ELORatingSystem = None):
        self.elo_system = elo_system or ELORatingSystem()
    
    def calculate_player_stats(self, player_tag: str) -> Dict[str, Any]:
        """Calculate comprehensive statistics for a player."""
        battles = self._get_player_battles(player_tag)
        
        if not battles:
            return {
                'wins': 0,
                'losses': 0,
                'total_crowns': 0,
                'elo_rating': self.elo_system.initial_rating,
                'current_streak': 0,
                'longest_streak': 0,
                'winrate': 0.0,
                'recent_form': [],
                'crown_differential': 0
            }
        
        # Sort battles by timestamp
        battles.sort(key=lambda x: x.timestamp)
        
        # Calculate basic stats
        wins = sum(1 for battle in battles if battle.winner == player_tag)
        losses = sum(1 for battle in battles if battle.loser == player_tag)
        total_crowns = sum(battle.crowns for battle in battles if battle.winner == player_tag)
        
        # Calculate streaks
        current_streak, longest_streak = self._calculate_streaks(battles, player_tag)
        
        # Calculate ELO rating
        elo_rating = self._calculate_elo_rating(battles, player_tag)
        
        # Calculate recent form (last 10 matches)
        recent_form = self._calculate_recent_form(battles, player_tag)
        
        # Calculate crown differential
        crown_differential = self._calculate_crown_differential(battles, player_tag)
        
        return {
            'wins': wins,
            'losses': losses,
            'total_crowns': total_crowns,
            'elo_rating': elo_rating,
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'winrate': (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0,
            'recent_form': recent_form,
            'crown_differential': crown_differential
        }
    
    def _get_player_battles(self, player_tag: str) -> List[Battle]:
        """Get all battles for a player from the database."""
        all_battles = db_manager.get_recent_battles(limit=1000)  # This now filters to today's battles only
        return [battle for battle in all_battles 
                if battle.player1 == player_tag or battle.player2 == player_tag]
    
    def _calculate_streaks(self, battles: List[Battle], player_tag: str) -> tuple[int, int]:
        """Calculate current and longest win streaks."""
        if not battles:
            return 0, 0
        
        # Sort by timestamp (most recent first) for current streak calculation
        battles.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Calculate current streak (from most recent games)
        current_streak = 0
        for battle in battles:
            if battle.winner == player_tag:
                if current_streak >= 0:  # Continue or start win streak
                    current_streak += 1
                else:  # Break loss streak, start win streak
                    current_streak = 1
            elif battle.loser == player_tag:
                if current_streak <= 0:  # Continue or start loss streak
                    current_streak -= 1
                else:  # Break win streak, start loss streak
                    current_streak = -1
            else:
                break  # Stop at first non-participating game
        
        # Calculate longest streak (from all games chronologically)
        battles.sort(key=lambda x: x.timestamp)  # Sort chronologically for longest streak
        longest_streak = 0
        temp_win_streak = 0
        
        for battle in battles:
            if battle.winner == player_tag:
                temp_win_streak += 1
                longest_streak = max(longest_streak, temp_win_streak)
            elif battle.loser == player_tag:
                temp_win_streak = 0  # Reset win streak on loss
        
        return current_streak, longest_streak
    
    def _calculate_elo_rating(self, battles: List[Battle], player_tag: str) -> float:
        """Calculate ELO rating for a player."""
        current_rating = self.elo_system.initial_rating
        
        # Sort battles chronologically
        battles.sort(key=lambda x: x.timestamp)
        
        for battle in battles:
            if battle.player1 == player_tag:
                opponent_rating = self._get_opponent_rating(battle.player2)
            elif battle.player2 == player_tag:
                opponent_rating = self._get_opponent_rating(battle.player1)
            else:
                continue
            
            if battle.winner == player_tag:
                current_rating, _, elo_change_winner, elo_change_loser = self.elo_system.update_ratings(current_rating, opponent_rating)
                # Store ELO changes in battle if not already set
                if battle.elo_change_winner is None:
                    battle.elo_change_winner = elo_change_winner
                    battle.elo_change_loser = elo_change_loser
                    # Update database with ELO changes
                    db_manager.update_battle_elo_changes(battle.match_id, elo_change_winner, elo_change_loser)
            else:
                _, current_rating, elo_change_winner, elo_change_loser = self.elo_system.update_ratings(opponent_rating, current_rating)
                # Store ELO changes in battle if not already set
                if battle.elo_change_winner is None:
                    battle.elo_change_winner = elo_change_winner
                    battle.elo_change_loser = elo_change_loser
                    # Update database with ELO changes
                    db_manager.update_battle_elo_changes(battle.match_id, elo_change_winner, elo_change_loser)
        
        return current_rating
    
    def _get_opponent_rating(self, opponent_tag: str) -> float:
        """Get current ELO rating of an opponent."""
        stats = db_manager.get_player_stats(opponent_tag)
        return stats.get('elo_rating', self.elo_system.initial_rating) if stats else self.elo_system.initial_rating
    
    def _calculate_recent_form(self, battles: List[Battle], player_tag: str, matches: int = 10) -> List[str]:
        """Calculate recent form (W/L for last N matches)."""
        if not battles:
            return []
        
        # Sort by timestamp (most recent first)
        battles.sort(key=lambda x: x.timestamp, reverse=True)
        
        recent_battles = battles[:matches]
        form = []
        
        for battle in recent_battles:
            if battle.winner == player_tag:
                form.append('W')
            elif battle.loser == player_tag:
                form.append('L')
        
        return form
    
    def _calculate_crown_differential(self, battles: List[Battle], player_tag: str) -> int:
        """Calculate crown differential (crowns scored - crowns conceded)."""
        crowns_scored = 0
        crowns_conceded = 0
        
        for battle in battles:
            if battle.winner == player_tag:
                crowns_scored += battle.crowns
            elif battle.loser == player_tag:
                # Find the opponent's crowns
                if battle.player1 == player_tag:
                    opponent_crowns = self._get_opponent_crowns(battle, battle.player2)
                else:
                    opponent_crowns = self._get_opponent_crowns(battle, battle.player1)
                crowns_conceded += opponent_crowns
        
        return crowns_scored - crowns_conceded
    
    def _get_opponent_crowns(self, battle: Battle, opponent_tag: str) -> int:
        """Get crowns scored by opponent in a battle."""
        # This is a simplified version - in a real implementation,
        # you'd need to store both players' crowns in the database
        return 3 - battle.crowns  # Assuming 3-crown games
    
    def update_all_player_stats(self, player_tags: List[str]):
        """Update statistics for all players."""
        for player_tag in player_tags:
            try:
                stats = self.calculate_player_stats(player_tag)
                db_manager.update_player_stats(player_tag, stats)
                logger.info(f"Updated stats for {player_tag}: {stats['wins']}W-{stats['losses']}L, ELO: {stats['elo_rating']:.1f}")
            except Exception as e:
                logger.error(f"Error updating stats for {player_tag}: {e}")


# Global instances
elo_system = ELORatingSystem()
stats_calculator = StatisticsCalculator(elo_system)
