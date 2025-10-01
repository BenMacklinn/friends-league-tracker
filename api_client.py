"""Clash Royale API client with rate limiting and error handling."""

import time
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API requests."""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests = []
    
    def wait_if_needed(self):
        """Wait if we've exceeded the rate limit."""
        now = time.time()
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests if now - req_time < 60]
        
        if len(self.requests) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.requests[0]) + 1
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
        
        self.requests.append(now)


class ClashRoyaleAPI:
    """Clash Royale API client."""
    
    def __init__(self, api_token: str, base_url: str = None, rate_limit: int = None):
        self.api_token = api_token
        self.base_url = base_url or settings.clash_royale_api_base_url
        self.rate_limiter = RateLimiter(rate_limit or settings.rate_limit_requests_per_minute)
        self.session = requests.Session()
        
        # Log proxy usage
        if settings.use_royaleapi_proxy:
            logger.info(f"Using RoyaleAPI proxy: {self.base_url}")
        else:
            logger.info(f"Using direct Clash Royale API: {self.base_url}")
        
        self.session.headers.update({
            'Authorization': f'Bearer {api_token}',
            'Accept': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make a rate-limited API request."""
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.get(url, params=params or {})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def get_player_info(self, player_tag: str) -> Optional[Dict[str, Any]]:
        """Get player information."""
        # Remove # from tag if present
        clean_tag = player_tag.replace('#', '')
        return self._make_request(f"/players/%23{clean_tag}")
    
    def get_player_battlelog(self, player_tag: str) -> Optional[List[Dict[str, Any]]]:
        """Get player battle log."""
        # Remove # from tag if present
        clean_tag = player_tag.replace('#', '')
        return self._make_request(f"/players/%23{clean_tag}/battlelog")
    
    def get_clan_info(self, clan_tag: str) -> Optional[Dict[str, Any]]:
        """Get clan information."""
        # Remove # from tag if present
        clean_tag = clan_tag.replace('#', '')
        return self._make_request(f"/clans/%23{clean_tag}")


class BattleProcessor:
    """Processes battle logs and filters relevant matches."""
    
    def __init__(self, api_client: ClashRoyaleAPI, friends_list: List[str]):
        self.api_client = api_client
        self.friends_list = [tag.replace('#', '') for tag in friends_list]
        self.friends_set = set(self.friends_list)
    
    def is_friends_match(self, battle: Dict[str, Any]) -> bool:
        """Check if both players in the battle are friends."""
        try:
            # Get player tags from battle data
            team1 = battle.get('team', [])
            team2 = battle.get('opponent', [])
            
            if not team1 or not team2:
                return False
            
            player1_tag = team1[0].get('tag', '').replace('#', '')
            player2_tag = team2[0].get('tag', '').replace('#', '')
            
            return (player1_tag in self.friends_set and 
                   player2_tag in self.friends_set)
        except (KeyError, IndexError, TypeError):
            return False
    
    def extract_battle_info(self, battle: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract relevant information from a battle."""
        try:
            team1 = battle.get('team', [])
            team2 = battle.get('opponent', [])
            
            if not team1 or not team2:
                return None
            
            player1 = team1[0]
            player2 = team2[0]
            
            # Determine winner
            crowns1 = battle.get('team', [{}])[0].get('crowns', 0)
            crowns2 = battle.get('opponent', [{}])[0].get('crowns', 0)
            
            if crowns1 > crowns2:
                winner = player1['tag'].replace('#', '')
                loser = player2['tag'].replace('#', '')
                crowns = crowns1
            elif crowns2 > crowns1:
                winner = player2['tag'].replace('#', '')
                loser = player1['tag'].replace('#', '')
                crowns = crowns2
            else:
                # Draw - skip for now
                return None
            
            # Extract deck information
            deck1 = self._extract_deck(team1)
            deck2 = self._extract_deck(team2)
            
            # Create deterministic match ID by sorting player tags
            sorted_tags = sorted([player1['tag'].replace('#', ''), player2['tag'].replace('#', '')])
            return {
                'match_id': battle.get('battleTime', '') + '_' + '_'.join(sorted_tags),
                'timestamp': datetime.fromisoformat(battle.get('battleTime', '').replace('Z', '+00:00')),
                'player1': player1['tag'].replace('#', ''),
                'player2': player2['tag'].replace('#', ''),
                'winner': winner,
                'loser': loser,
                'crowns': crowns,
                'battle_type': battle.get('type', 'unknown'),
                'deck1': deck1,
                'deck2': deck2
            }
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error extracting battle info: {e}")
            return None
    
    def _extract_deck(self, team: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract deck information from team data."""
        try:
            if not team:
                return None
            
            player = team[0]
            cards = player.get('cards', [])
            
            if not cards:
                return None
            
            return {
                'cards': [card.get('name', '') for card in cards],
                'elixir_cost': sum(card.get('elixirCost', 0) for card in cards) / len(cards) if cards else 0
            }
        except (KeyError, TypeError):
            return None
    
    def process_player_battles(self, player_tag: str) -> List[Dict[str, Any]]:
        """Process battles for a specific player."""
        battlelog = self.api_client.get_player_battlelog(player_tag)
        if not battlelog:
            return []
        
        # Only process battles from today forward (new season)
        today = datetime.now().date()
        
        relevant_battles = []
        for battle in battlelog:
            if self.is_friends_match(battle):
                battle_info = self.extract_battle_info(battle)
                if battle_info:
                    # Filter out battles from before today
                    battle_date = battle_info['timestamp'].date()
                    if battle_date >= today:
                        relevant_battles.append(battle_info)
        
        return relevant_battles
    
    def process_all_friends_battles(self) -> List[Dict[str, Any]]:
        """Process battles for all friends."""
        all_battles = []
        
        for player_tag in self.friends_list:
            logger.info(f"Processing battles for player: {player_tag}")
            battles = self.process_player_battles(player_tag)
            all_battles.extend(battles)
        
        # Remove duplicates based on match_id
        seen_ids = set()
        unique_battles = []
        for battle in all_battles:
            if battle['match_id'] not in seen_ids:
                seen_ids.add(battle['match_id'])
                unique_battles.append(battle)
        
        return unique_battles


# Global API client instance
api_client = ClashRoyaleAPI(
    api_token=settings.clash_royale_api_token,
    base_url=settings.clash_royale_api_base_url,
    rate_limit=settings.rate_limit_requests_per_minute
)
