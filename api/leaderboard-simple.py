"""Simple leaderboard endpoint for testing."""

import json


def handler(request):
    """Simple leaderboard handler for testing."""
    # Return mock data to test if the endpoint works
    mock_data = {
        "players": [
            {
                "player_tag": "TEST123",
                "name": "Test Player",
                "wins": 5,
                "losses": 3,
                "total_crowns": 15,
                "elo_rating": 1250.0,
                "current_streak": 2,
                "longest_streak": 3,
                "winrate": 62.5
            }
        ],
        "last_updated": "2025-01-27T00:00:00Z",
        "total_matches": 8
    }
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(mock_data)
    }
