"""Command-line interface for Friends League tracker."""

import argparse
import sys
import sqlite3
from typing import List, Dict, Any
from datetime import timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from tabulate import tabulate

from database import db_manager
from ranking_system import stats_calculator
from config import settings

console = Console()


def display_leaderboard(limit: int = None, format_type: str = "rich"):
    """Display the leaderboard in various formats."""
    try:
        all_stats = db_manager.get_all_player_stats()
        
        if limit:
            all_stats = all_stats[:limit]
        
        if not all_stats:
            console.print("[yellow]No player statistics found. Run data collection first.[/yellow]")
            return
        
        if format_type == "rich":
            _display_rich_leaderboard(all_stats)
        elif format_type == "table":
            _display_table_leaderboard(all_stats)
        elif format_type == "json":
            _display_json_leaderboard(all_stats)
        else:
            console.print(f"[red]Unknown format: {format_type}[/red]")
    
    except Exception as e:
        console.print(f"[red]Error displaying leaderboard: {e}[/red]")


def _display_rich_leaderboard(stats: List[Dict[str, Any]]):
    """Display leaderboard using Rich formatting."""
    table = Table(title="🏆 Friends League Leaderboard", show_header=True, header_style="bold magenta")
    
    table.add_column("Rank", style="dim", width=6)
    table.add_column("Player", style="cyan", width=15)
    table.add_column("W-L", style="green", width=8)
    table.add_column("Winrate", style="yellow", width=8)
    table.add_column("ELO", style="blue", width=8)
    table.add_column("Crowns", style="magenta", width=8)
    
    for i, player in enumerate(stats, 1):
        # Color code based on rank
        if i == 1:
            rank_style = "bold gold1"
        elif i <= 3:
            rank_style = "bold yellow"
        else:
            rank_style = "dim"
        
        # Format winrate
        winrate_text = f"{player['winrate']:.1f}%"
        
        table.add_row(
            Text(str(i), style=rank_style),
            player['name'] or player['player_tag'],
            f"{player['wins']}-{player['losses']}",
            winrate_text,
            f"{player['elo_rating']:.0f}",
            str(player['total_crowns'])
        )
    
    console.print(table)


def _display_table_leaderboard(stats: List[Dict[str, Any]]):
    """Display leaderboard using tabulate."""
    headers = ["Rank", "Player", "W-L", "Winrate%", "ELO", "Crowns"]
    rows = []
    
    for i, player in enumerate(stats, 1):
        rows.append([
            i,
            player['name'] or player['player_tag'],
            f"{player['wins']}-{player['losses']}",
            f"{player['winrate']:.1f}",
            f"{player['elo_rating']:.0f}",
            player['total_crowns']
        ])
    
    print(tabulate(rows, headers=headers, tablefmt="grid"))


def _display_json_leaderboard(stats: List[Dict[str, Any]]):
    """Display leaderboard as JSON."""
    import json
    print(json.dumps(stats, indent=2))


def display_player_stats(player_tag: str):
    """Display detailed stats for a specific player."""
    try:
        clean_tag = player_tag.replace('#', '')
        stats = db_manager.get_player_stats(clean_tag)
        
        if not stats:
            console.print(f"[red]Player {player_tag} not found.[/red]")
            return
        
        # Create a detailed panel
        content = f"""
[bold]Player:[/bold] {clean_tag}
[bold]Record:[/bold] {stats['wins']}W - {stats['losses']}L
[bold]Winrate:[/bold] {stats['winrate']:.1f}%
[bold]ELO Rating:[/bold] {stats['elo_rating']:.1f}
[bold]Current Streak:[/bold] {stats['current_streak']} {'Wins' if stats['current_streak'] > 0 else 'Losses'}
[bold]Longest Streak:[/bold] {stats['longest_streak']} Wins
[bold]Total Crowns:[/bold] {stats['total_crowns']}
        """
        
        panel = Panel(content, title=f"📊 {clean_tag} Statistics", border_style="blue")
        console.print(panel)
    
    except Exception as e:
        console.print(f"[red]Error displaying player stats: {e}[/red]")


def display_recent_battles(limit: int = 10):
    """Display recent battles."""
    try:
        battles = db_manager.get_recent_battles(limit=limit)
        
        if not battles:
            console.print("[yellow]No recent battles found.[/yellow]")
            return
        
        table = Table(title="⚔️ Recent Battles", show_header=True, header_style="bold magenta")
        table.add_column("Time", style="dim", width=12)
        table.add_column("Players", style="cyan", width=25)
        table.add_column("Winner", style="green", width=15)
        table.add_column("Crowns", style="yellow", width=8)
        table.add_column("Type", style="blue", width=12)
        
        for battle in battles:
            # Convert UTC to local time
            local_time = battle.timestamp.replace(tzinfo=None) - timedelta(hours=4)  # EDT is UTC-4
            time_str = local_time.strftime("%m/%d %H:%M")
            
            # Get player names from database
            player1_name = _get_player_name(battle.player1)
            player2_name = _get_player_name(battle.player2)
            winner_name = _get_player_name(battle.winner)
            
            players = f"{player1_name} vs {player2_name}"
            
            table.add_row(
                time_str,
                players,
                winner_name,
                str(battle.crowns),
                battle.battle_type
            )
        
        console.print(table)
    
    except Exception as e:
        console.print(f"[red]Error displaying recent battles: {e}[/red]")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Friends League Tracker CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Leaderboard command
    leaderboard_parser = subparsers.add_parser("leaderboard", help="Display leaderboard")
    leaderboard_parser.add_argument("--limit", type=int, help="Limit number of players shown")
    leaderboard_parser.add_argument("--format", choices=["rich", "table", "json"], default="rich", help="Output format")
    
    # Player stats command
    player_parser = subparsers.add_parser("player", help="Display player statistics")
    player_parser.add_argument("tag", help="Player tag")
    
    # Recent battles command
    battles_parser = subparsers.add_parser("battles", help="Display recent battles")
    battles_parser.add_argument("--limit", type=int, default=10, help="Number of battles to show")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Display current configuration")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "leaderboard":
        display_leaderboard(limit=args.limit, format_type=args.format)
    elif args.command == "player":
        display_player_stats(args.tag)
    elif args.command == "battles":
        display_recent_battles(limit=args.limit)
    elif args.command == "config":
        _display_config()
    else:
        parser.print_help()


def _get_player_name(player_tag: str) -> str:
    """Get player name from database, fallback to tag if not found."""
    try:
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM players WHERE tag = ?", (player_tag,))
            result = cursor.fetchone()
            return result[0] if result and result[0] else player_tag
    except Exception:
        return player_tag


def _display_config():
    """Display current configuration."""
    config_info = f"""
[bold]Configuration:[/bold]
API Base URL: {settings.clash_royale_api_base_url}
Database Path: {settings.database_path}
Polling Interval: {settings.polling_interval_minutes} minutes
Rate Limit: {settings.rate_limit_requests_per_minute} requests/minute
Player Tags: {', '.join(settings.get_player_tags_list())}
    """
    
    panel = Panel(config_info, title="⚙️ Configuration", border_style="green")
    console.print(panel)


if __name__ == "__main__":
    main()
