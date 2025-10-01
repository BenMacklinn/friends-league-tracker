"""Main entry point for Friends League Tracker."""

import argparse
import sys
import logging
from typing import List

from config import settings
from database import db_manager
from api_client import api_client
from background_scheduler import DataCollector
from cli import display_leaderboard, display_player_stats, display_recent_battles

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('friends_league.log'),
            logging.StreamHandler()
        ]
    )


def run_server(host=None, port=None):
    """Run the FastAPI server."""
    import uvicorn
    from api_server import app
    
    # Use provided host/port or fall back to settings
    server_host = host or settings.host
    server_port = port or settings.port
    
    logger.info(f"Starting server on {server_host}:{server_port}")
    uvicorn.run(
        app,
        host=server_host,
        port=server_port,
        log_level="info"
    )




def collect_data_once():
    """Run data collection once."""
    # Check if we have player tags configured
    player_tags = settings.get_player_tags_list()
    if not player_tags:
        logger.error("No player tags configured. Please set PLAYER_TAGS environment variable.")
        return
    
    logger.info(f"Running one-time data collection for {len(player_tags)} players")
    
    data_collector = DataCollector()
    data_collector.collect_and_process_data()


def add_player(player_tag: str):
    """Add a new player to the friends list."""
    data_collector = DataCollector()
    success = data_collector.add_player(player_tag)
    
    if success:
        print(f"Successfully added player {player_tag}")
    else:
        print(f"Failed to add player {player_tag}")
        sys.exit(1)


def show_leaderboard(limit: int = None, format_type: str = "rich"):
    """Show the leaderboard."""
    display_leaderboard(limit=limit, format_type=format_type)


def show_player_stats(player_tag: str):
    """Show player statistics."""
    display_player_stats(player_tag)


def show_recent_battles(limit: int = 10):
    """Show recent battles."""
    display_recent_battles(limit=limit)


def run_web_server(port: int = 3000, no_browser: bool = False):
    """Run the web server."""
    from web_server import start_web_server
    
    if no_browser:
        # Monkey patch webbrowser to prevent opening
        import webbrowser
        webbrowser.open = lambda url: None
    
    start_web_server(port)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Friends League Tracker")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Run the API server")
    server_parser.add_argument("--host", default=settings.host, help="Host to bind to")
    server_parser.add_argument("--port", type=int, default=settings.port, help="Port to bind to")
    
    
    # Collect command
    collect_parser = subparsers.add_parser("collect", help="Run data collection once (use this daily)")
    
    # Add player command
    add_player_parser = subparsers.add_parser("add-player", help="Add a new player")
    add_player_parser.add_argument("tag", help="Player tag to add")
    
    # Leaderboard command
    leaderboard_parser = subparsers.add_parser("leaderboard", help="Show leaderboard")
    leaderboard_parser.add_argument("--limit", type=int, help="Limit number of players")
    leaderboard_parser.add_argument("--format", choices=["rich", "table", "json"], default="rich", help="Output format")
    
    # Player stats command
    player_parser = subparsers.add_parser("player", help="Show player statistics")
    player_parser.add_argument("tag", help="Player tag")
    
    # Recent battles command
    battles_parser = subparsers.add_parser("battles", help="Show recent battles")
    battles_parser.add_argument("--limit", type=int, default=10, help="Number of battles to show")
    
    # Web server command
    web_parser = subparsers.add_parser("web", help="Start the web interface")
    web_parser.add_argument("--port", type=int, default=3000, help="Port for the web server")
    web_parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    # Log level
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "server":
            run_server(host=args.host, port=args.port)
        elif args.command == "collect":
            collect_data_once()
        elif args.command == "add-player":
            add_player(args.tag)
        elif args.command == "leaderboard":
            show_leaderboard(limit=args.limit, format_type=args.format)
        elif args.command == "player":
            show_player_stats(args.tag)
        elif args.command == "battles":
            show_recent_battles(limit=args.limit)
        elif args.command == "web":
            run_web_server(port=args.port, no_browser=args.no_browser)
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
