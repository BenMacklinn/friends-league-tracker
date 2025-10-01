def handler(request):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": '[{"match_id":"test_match_1","timestamp":"2025-01-27T00:00:00Z","player1":"TEST123","player2":"TEST456","winner":"TEST123","loser":"TEST456","crowns":2,"battle_type":"1v1","elo_change_winner":15.5,"elo_change_loser":-15.5}]'
    }
