# Vercel Deployment Guide

This guide will help you deploy the Friends League Tracker to Vercel with automatic 30-minute data collection.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Push your code to GitHub
3. **Clash Royale API Token**: Get one from [developer.clashroyale.com](https://developer.clashroyale.com)
4. **RoyaleAPI Proxy**: Recommended for Vercel deployment

## Step 1: Prepare Your Repository

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Add Vercel deployment configuration"
   git push origin main
   ```

2. **Enable RoyaleAPI Proxy** (Recommended):
   - Set `USE_ROYALEAPI_PROXY=true` in your environment
   - Whitelist IP `45.79.218.79` in your Clash Royale API key settings

## Step 2: Deploy to Vercel

1. **Connect Repository**:
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Environment Variables**:
   In the Vercel dashboard, go to Settings → Environment Variables and add:

   ```
   CLASH_ROYALE_API_TOKEN=your_api_token_here
   USE_ROYALEAPI_PROXY=true
   ROYALEAPI_PROXY_URL=https://proxy.royaleapi.dev
   PLAYER_TAGS=C0G20PR2,ABC123,XYZ789
   DATABASE_PATH=/tmp/friends_league.db
   RATE_LIMIT_REQUESTS_PER_MINUTE=10
   ```

3. **Deploy**:
   - Click "Deploy"
   - Wait for the deployment to complete

## Step 3: Verify Deployment

1. **Check API Endpoints**:
   ```bash
   # Test leaderboard
   curl https://your-app.vercel.app/api/leaderboard/
   
   # Test battles
   curl https://your-app.vercel.app/api/battles/recent
   ```

2. **Check Cron Job**:
   - Go to Vercel Dashboard → Functions
   - Look for the cron job in the logs
   - It should run every 30 minutes

## Step 4: Access Your Application

- **Web Interface**: `https://your-app.vercel.app`
- **API Base**: `https://your-app.vercel.app/api`
- **Leaderboard**: `https://your-app.vercel.app/api/leaderboard/`
- **Recent Battles**: `https://your-app.vercel.app/api/battles/recent`

## Configuration Details

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `CLASH_ROYALE_API_TOKEN` | Your Clash Royale API token | Yes | - |
| `USE_ROYALEAPI_PROXY` | Enable RoyaleAPI proxy | No | `false` |
| `ROYALEAPI_PROXY_URL` | Proxy URL | No | `https://proxy.royaleapi.dev` |
| `PLAYER_TAGS` | Comma-separated player tags | Yes | - |
| `DATABASE_PATH` | Database file path | No | `/tmp/friends_league.db` |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | API rate limit | No | `10` |

### Cron Schedule

The application automatically collects data every 30 minutes using Vercel's cron jobs:

```json
{
  "crons": [
    {
      "path": "/api/cron/collect",
      "schedule": "*/30 * * * *"
    }
  ]
}
```

### File Structure

```
├── api/
│   ├── leaderboard.py      # Leaderboard API endpoint
│   ├── battles.py          # Battles API endpoint
│   └── cron/
│       └── collect.py      # Cron job for data collection
├── web/
│   ├── index.html          # Web interface
│   ├── script.js           # Frontend JavaScript
│   └── style.css           # Styles
├── vercel.json             # Vercel configuration
└── requirements.txt        # Python dependencies
```

## Troubleshooting

### Common Issues

1. **"API token not configured"**:
   - Check environment variables in Vercel dashboard
   - Ensure `CLASH_ROYALE_API_TOKEN` is set

2. **"No player tags configured"**:
   - Set `PLAYER_TAGS` environment variable
   - Use comma-separated tags without spaces

3. **"403 Forbidden" errors**:
   - Enable RoyaleAPI proxy: `USE_ROYALEAPI_PROXY=true`
   - Whitelist IP `45.79.218.79` in your API key settings

4. **Cron job not running**:
   - Check Vercel Functions logs
   - Verify cron schedule in `vercel.json`
   - Ensure the cron endpoint is accessible

### Monitoring

1. **Vercel Dashboard**:
   - Go to Functions tab to see cron job logs
   - Check Analytics for usage statistics

2. **Application Logs**:
   - View function logs in Vercel dashboard
   - Check for errors in data collection

## Customization

### Change Cron Schedule

Edit `vercel.json` to modify the cron schedule:

```json
{
  "crons": [
    {
      "path": "/api/cron/collect",
      "schedule": "0 */2 * * *"  // Every 2 hours
    }
  ]
}
```

### Add More API Endpoints

Create new files in the `api/` directory following the existing pattern.

### Custom Domain

1. Go to Vercel Dashboard → Domains
2. Add your custom domain
3. Configure DNS settings

## Support

- **Vercel Documentation**: [vercel.com/docs](https://vercel.com/docs)
- **RoyaleAPI Proxy**: [docs.royaleapi.com/proxy.html](https://docs.royaleapi.com/proxy.html)
- **Clash Royale API**: [developer.clashroyale.com](https://developer.clashroyale.com)

---

**Happy Deploying!** 🚀
