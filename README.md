# Friends League Tracker

A comprehensive Clash Royale "Friends League" tracker with dynamic power rankings leaderboard. This application tracks battles between friends, calculates ELO ratings, and provides a beautiful leaderboard interface.

## Features

- 🏆 **Dynamic Leaderboard**: Real-time ELO-based rankings
- ⚔️ **Battle Tracking**: Automatically tracks matches between friends
- 📊 **Statistics**: Win/loss records, streaks, crown differentials
- 🔄 **Auto-Update**: 30-minute automatic data collection (Vercel)
- 🌐 **API Server**: RESTful API for leaderboard data
- 💻 **CLI Interface**: Command-line tools for viewing stats
- 🛡️ **Rate Limiting**: Respects Clash Royale API limits
- 📱 **Modern UI**: Rich terminal output and web interface
- ☁️ **Cloud Ready**: Deploy to Vercel with zero configuration
- 🔗 **RoyaleAPI Proxy**: No IP restrictions, works from anywhere

## Quick Start

### Option 1: Local Development

```bash
# Clone the repository
git clone <repository-url>
cd CRPR

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Deploy to Vercel (Recommended)

For automatic 30-minute data collection and global accessibility:

1. **Push to GitHub** and connect to Vercel
2. **Set environment variables** in Vercel dashboard
3. **Deploy** - your app will be live with auto-scraping!

See [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) for detailed instructions.

### 3. Configuration

Create a `.env` file with your Clash Royale API token and player tags:

```env
# Clash Royale API Configuration
CLASH_ROYALE_API_TOKEN=your_api_token_here

# RoyaleAPI Proxy Configuration (Optional)
# Set to "true" to use RoyaleAPI proxy instead of direct API calls
# Useful if your server doesn't have a static IP address
USE_ROYALEAPI_PROXY=false
ROYALEAPI_PROXY_URL=https://proxy.royaleapi.dev

# Direct API URL (only used if USE_ROYALEAPI_PROXY=false)
CLASH_ROYALE_API_BASE_URL=https://api.clashroyale.com/v1

# Player tags (comma-separated)
PLAYER_TAGS=#ABC123,#DEF456,#GHI789

# Application Configuration
DATABASE_PATH=./data/friends_league.db
POLLING_INTERVAL_MINUTES=15
RATE_LIMIT_REQUESTS_PER_MINUTE=10

# Server Configuration
HOST=127.0.0.1
PORT=8000
```

**Note**: Copy `env.example` to `.env` and fill in your values.

### 4. Get Your API Token

1. Visit [Clash Royale API](https://developer.clashroyale.com/)
2. Create an account and generate an API token
3. Add the token to your `.env` file

### 5. RoyaleAPI Proxy Setup (Optional)

If your server doesn't have a static IP address, you can use the RoyaleAPI proxy to access the Clash Royale API:

1. **Enable the proxy** in your `.env` file:
   ```env
   USE_ROYALEAPI_PROXY=true
   ```

2. **Whitelist the proxy IP** in your Clash Royale API key settings:
   - Go to [Clash Royale API Developer Portal](https://developer.clashroyale.com/)
   - Edit your API key
   - Add this IP address: `45.79.218.79`
   - Save the changes

3. **Use your existing API token** - no changes needed to your token

The proxy will automatically route your API requests through RoyaleAPI's servers, eliminating the need for IP whitelisting.

**Benefits of using the proxy:**
- No need for static IP addresses
- Works from any location
- Automatic failover and load balancing
- Community support available

For more information, visit the [RoyaleAPI Proxy Documentation](https://docs.royaleapi.com/proxy.html).

### 6. Run the Application

```bash
# Collect data once (run this daily when you're at home)
python main.py collect

# Run the API server
python main.py server

# Start the web interface
python main.py web
```

## Usage

### Command Line Interface

```bash
# Show leaderboard
python main.py leaderboard

# Show leaderboard with limit
python main.py leaderboard --limit 10

# Show player statistics
python main.py player #ABC123

# Show recent battles
python main.py battles --limit 20

# Add a new player
python main.py add-player #NEW123
```

### API Endpoints

When running the server (`python main.py server`), the following endpoints are available:

- `GET /` - API information
- `GET /health` - Health check
- `GET /leaderboard` - Get current leaderboard
- `GET /player/{tag}` - Get player statistics
- `GET /battles/recent` - Get recent battles
- `POST /refresh` - Trigger data refresh

### Example API Usage

```bash
# Get leaderboard
curl http://localhost:8000/leaderboard

# Get player stats
curl http://localhost:8000/player/ABC123

# Get recent battles
curl http://localhost:8000/battles/recent?limit=10
```

## Project Structure

```
CRPR/
├── main.py                 # Main entry point
├── config.py              # Configuration management
├── database.py            # Database models and operations
├── api_client.py          # Clash Royale API client
├── ranking_system.py      # ELO rating and statistics
├── api_server.py          # FastAPI server
├── cli.py                 # Command-line interface
├── background_scheduler.py # Data collection utilities
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Database Schema

The application uses SQLite with the following tables:

- **players**: Player information (tag, name, trophies)
- **battles**: Battle records (match_id, players, winner, etc.)
- **player_stats**: Computed statistics (wins, losses, ELO, streaks)

## ELO Rating System

The application uses a standard ELO rating system:

- **Initial Rating**: 1200
- **K-Factor**: 32 (adjustable)
- **Rating Updates**: After each battle
- **Expected Score**: Based on rating difference

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `CLASH_ROYALE_API_TOKEN` | Your API token | Required |
| `PLAYER_TAGS` | Comma-separated player tags | Required |
| `USE_ROYALEAPI_PROXY` | Use RoyaleAPI proxy instead of direct API | `false` |
| `ROYALEAPI_PROXY_URL` | RoyaleAPI proxy URL | `https://proxy.royaleapi.dev` |
| `CLASH_ROYALE_API_BASE_URL` | Direct API URL (when proxy disabled) | `https://api.clashroyale.com/v1` |
| `POLLING_INTERVAL_MINUTES` | (Deprecated - no longer used) | 15 |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | API rate limit | 10 |
| `DATABASE_PATH` | SQLite database location | `./data/friends_league.db` |

## Advanced Features

### Custom ELO Parameters

Modify `ranking_system.py` to adjust ELO settings:

```python
elo_system = ELORatingSystem(
    initial_rating=1200.0,  # Starting rating
    k_factor=32.0          # Rating change multiplier
)
```

### Battle Filtering

The system automatically filters battles to only include matches where both players are in your friends list. This ensures the leaderboard only reflects games between your group.

### Daily Data Collection

Since the API requires IP restrictions, run `python main.py collect` daily when you're at home to update the leaderboard with new battles.

### Rate Limiting

The API client includes built-in rate limiting to respect Clash Royale's API quotas. Adjust the `RATE_LIMIT_REQUESTS_PER_MINUTE` setting as needed.

## Troubleshooting

### Common Issues

1. **"No player tags configured"**
   - Set the `PLAYER_TAGS` environment variable
   - Use comma-separated tags without spaces

2. **"API request failed"**
   - Check your API token
   - Verify the token has the correct permissions
   - Check rate limiting settings

3. **"Player not found"**
   - Verify player tags are correct
   - Ensure players have recent battle history
   - Check if players are in the same region

4. **"API request failed: 403 Forbidden"**
   - Your IP address has changed
   - Update your API key to include your current IP address
   - Run data collection only when you're at home
   - **Solution**: Enable RoyaleAPI proxy by setting `USE_ROYALEAPI_PROXY=true` in your `.env` file

### Logs

The application creates a `friends_league.log` file with detailed information about:
- API requests and responses
- Database operations
- Error messages
- Data collection activity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Clash Royale API](https://developer.clashroyale.com/) for providing the data
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output

## Support

If you encounter any issues or have questions:

1. Check the troubleshooting section
2. Review the logs
3. Open an issue on GitHub
4. Contact the maintainers

---

**Happy Clashing!** 🏆⚔️
