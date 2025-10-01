"""Simple battles endpoint for testing."""

import json


def handler(request):
    """Simple battles handler for testing."""
    # Return mock data to test if the endpoint works
    mock_data = [
        {
            "match_id": "test_match_1",
            "timestamp": "2025-01-27T00:00:00Z",
            "player1": "TEST123",
            "player2": "TEST456",
            "winner": "TEST123",
            "loser": "TEST456",
            "crowns": 2,
            "battle_type": "1v1",
            "elo_change_winner": 15.5,
            "elo_change_loser": -15.5
        }
    ]
    
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
