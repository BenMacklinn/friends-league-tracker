def handler(request):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": '{"players":[{"player_tag":"TEST123","name":"Test Player","wins":5,"losses":3,"total_crowns":15,"elo_rating":1250.0,"current_streak":2,"longest_streak":3,"winrate":62.5}],"last_updated":"2025-01-27T00:00:00Z","total_matches":8}'
    }
