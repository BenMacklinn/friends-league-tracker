#!/usr/bin/env python3
"""Test script to verify RoyaleAPI proxy functionality."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from api_client import ClashRoyaleAPI

def test_proxy_configuration():
    """Test the proxy configuration."""
    print("=== RoyaleAPI Proxy Configuration Test ===\n")
    
    print(f"Use RoyaleAPI Proxy: {settings.use_royaleapi_proxy}")
    print(f"Proxy URL: {settings.royaleapi_proxy_url}")
    print(f"API Base URL: {settings.clash_royale_api_base_url}")
    print(f"API Token: {'*' * (len(settings.clash_royale_api_token) - 4) + settings.clash_royale_api_token[-4:] if settings.clash_royale_api_token else 'Not set'}")
    
    if not settings.clash_royale_api_token:
        print("\n❌ Error: CLASH_ROYALE_API_TOKEN not set!")
        print("Please set your API token in the .env file.")
        return False
    
    return True

def test_api_connection():
    """Test API connection with current configuration."""
    print("\n=== API Connection Test ===\n")
    
    try:
        # Create API client
        api_client = ClashRoyaleAPI(
            api_token=settings.clash_royale_api_token,
            base_url=settings.clash_royale_api_base_url,
            rate_limit=5  # Lower rate limit for testing
        )
        
        print(f"Testing connection to: {api_client.base_url}")
        
        # Test with a known player tag (RoyaleAPI's test tag)
        test_tag = "C0G20PR2"  # This is a commonly used test tag
        print(f"Testing with player tag: #{test_tag}")
        
        # Make a test request
        player_info = api_client.get_player_info(test_tag)
        
        if player_info:
            print("✅ API connection successful!")
            print(f"Player name: {player_info.get('name', 'Unknown')}")
            print(f"Player level: {player_info.get('expLevel', 'Unknown')}")
            print(f"Current trophies: {player_info.get('trophies', 'Unknown')}")
            return True
        else:
            print("❌ API request failed - no data returned")
            return False
            
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def main():
    """Main test function."""
    print("RoyaleAPI Proxy Test Script")
    print("=" * 40)
    
    # Test configuration
    if not test_proxy_configuration():
        sys.exit(1)
    
    # Test API connection
    if not test_api_connection():
        print("\n❌ Tests failed!")
        print("\nTroubleshooting tips:")
        print("1. Check your API token is correct")
        print("2. If using proxy, ensure your API key is whitelisted for IP: 45.79.218.79")
        print("3. If not using proxy, ensure your current IP is whitelisted")
        print("4. Check your internet connection")
        sys.exit(1)
    
    print("\n✅ All tests passed!")
    print("\nYour RoyaleAPI proxy configuration is working correctly.")

if __name__ == "__main__":
    main()
