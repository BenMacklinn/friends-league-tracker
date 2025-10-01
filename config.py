"""Configuration management for Friends League tracker."""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""
    
    def __init__(self):
        # Clash Royale API
        self.clash_royale_api_token = os.getenv("CLASH_ROYALE_API_TOKEN", "")
        
        # RoyaleAPI Proxy Configuration
        self.use_royaleapi_proxy = os.getenv("USE_ROYALEAPI_PROXY", "false").lower() == "true"
        self.royaleapi_proxy_url = os.getenv("ROYALEAPI_PROXY_URL", "https://proxy.royaleapi.dev")
        
        # Set base URL based on proxy configuration
        if self.use_royaleapi_proxy:
            self.clash_royale_api_base_url = self.royaleapi_proxy_url
        else:
            self.clash_royale_api_base_url = os.getenv(
                "CLASH_ROYALE_API_BASE_URL", 
                "https://api.clashroyale.com/v1"
            )
        
        # Database
        self.database_path = os.getenv("DATABASE_PATH", "./data/friends_league.db")
        
        # Polling
        self.polling_interval_minutes = int(os.getenv("POLLING_INTERVAL_MINUTES", "15"))
        self.rate_limit_requests_per_minute = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "10"))
        
        # Server
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = int(os.getenv("PORT", "8000"))
        
        # Player tags (comma-separated)
        self.player_tags = os.getenv("PLAYER_TAGS", "")
    
    def get_player_tags_list(self) -> List[str]:
        """Get player tags as a list."""
        if not self.player_tags:
            return []
        return [tag.strip() for tag in self.player_tags.split(",") if tag.strip()]


# Global settings instance
settings = Settings()
