"""Background scheduler for polling Clash Royale API."""

import asyncio
import schedule
import time
import logging
from datetime import datetime
from typing import List

from config import settings
from api_client import api_client, BattleProcessor
from database import db_manager, Battle
from ranking_system import stats_calculator

logger = logging.getLogger(__name__)


class DataCollector:
    """Collects and processes data from Clash Royale API."""
    
    def __init__(self):
        self.battle_processor = BattleProcessor(
            api_client=api_client,
            friends_list=settings.get_player_tags_list()
        )
    
    def collect_and_process_data(self):
        """Main data collection and processing function."""
        try:
            logger.info("Starting data collection...")
            
            # Get all friends' battle logs
            all_battles = self.battle_processor.process_all_friends_battles()
            logger.info(f"Found {len(all_battles)} relevant battles")
            
            # Add new battles to database
            new_battles_count = 0
            for battle_data in all_battles:
                battle = Battle(
                    match_id=battle_data['match_id'],
                    timestamp=battle_data['timestamp'],
                    player1=battle_data['player1'],
                    player2=battle_data['player2'],
                    winner=battle_data['winner'],
                    loser=battle_data['loser'],
                    crowns=battle_data['crowns'],
                    battle_type=battle_data['battle_type'],
                    deck1=battle_data.get('deck1'),
                    deck2=battle_data.get('deck2'),
                    elo_change_winner=battle_data.get('elo_change_winner'),
                    elo_change_loser=battle_data.get('elo_change_loser')
                )
                
                if db_manager.add_battle(battle):
                    new_battles_count += 1
            
            logger.info(f"Added {new_battles_count} new battles to database")
            
            # Update player statistics
            if new_battles_count > 0:
                self._update_player_statistics()
            
            logger.info("Data collection completed successfully")
            
        except Exception as e:
            logger.error(f"Error during data collection: {e}")
    
    def _update_player_statistics(self):
        """Update statistics for all players."""
        try:
            player_tags = settings.get_player_tags_list()
            stats_calculator.update_all_player_stats(player_tags)
            logger.info("Player statistics updated")
        except Exception as e:
            logger.error(f"Error updating player statistics: {e}")
    
    def add_player(self, player_tag: str):
        """Add a new player to the friends list."""
        try:
            # Get player info from API
            player_info = api_client.get_player_info(player_tag)
            if not player_info:
                logger.error(f"Could not fetch player info for {player_tag}")
                return False
            
            # Add to database
            db_manager.add_player(
                tag=player_tag.replace('#', ''),
                name=player_info.get('name'),
                trophies=player_info.get('trophies')
            )
            
            logger.info(f"Added player {player_tag} to friends list")
            return True
            
        except Exception as e:
            logger.error(f"Error adding player {player_tag}: {e}")
            return False


class Scheduler:
    """Background scheduler for data collection."""
    
    def __init__(self):
        self.data_collector = DataCollector()
        self.is_running = False
    
    def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        logger.info(f"Starting scheduler with {settings.polling_interval_minutes} minute intervals")
        
        # Schedule the data collection
        schedule.every(settings.polling_interval_minutes).minutes.do(
            self.data_collector.collect_and_process_data
        )
        
        # Run initial data collection
        logger.info("Running initial data collection...")
        self.data_collector.collect_and_process_data()
        
        # Start the scheduler loop
        self._run_scheduler()
    
    def stop(self):
        """Stop the scheduler."""
        self.is_running = False
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping scheduler...")
                self.stop()
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def run_once(self):
        """Run data collection once (for testing)."""
        logger.info("Running one-time data collection...")
        self.data_collector.collect_and_process_data()


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('friends_league.log'),
            logging.StreamHandler()
        ]
    )


def main():
    """Main entry point for the scheduler."""
    setup_logging()
    
    # Check if we have player tags configured
    player_tags = settings.get_player_tags_list()
    if not player_tags:
        logger.error("No player tags configured. Please set PLAYER_TAGS environment variable.")
        return
    
    logger.info(f"Starting Friends League Tracker for {len(player_tags)} players")
    
    # Create and start scheduler
    scheduler = Scheduler()
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        scheduler.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        scheduler.stop()


if __name__ == "__main__":
    main()
