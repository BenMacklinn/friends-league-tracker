"""Simple web server to serve the Friends League frontend."""

import os
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import webbrowser
import time

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import settings


class FriendsLeagueHandler(SimpleHTTPRequestHandler):
    """Custom handler for serving the Friends League web interface."""
    
    def __init__(self, *args, **kwargs):
        # Set the directory to serve from
        web_dir = project_root / "web"
        super().__init__(*args, directory=str(web_dir), **kwargs)
    
    def end_headers(self):
        # Add CORS headers for API access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # Serve index.html for root path
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()


def start_web_server(port=3000):
    """Start the web server."""
    try:
        server = HTTPServer(('localhost', port), FriendsLeagueHandler)
        print(f"🌐 Web server starting on http://localhost:{port}")
        print(f"📊 Friends League frontend is now available!")
        print(f"🔗 Open your browser and go to: http://localhost:{port}")
        print(f"⚡ Make sure the API server is running on port {settings.port}")
        print(f"🛑 Press Ctrl+C to stop the server")
        
        # Open browser automatically
        def open_browser():
            time.sleep(1)
            webbrowser.open(f'http://localhost:{port}')
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Web server stopped")
        server.shutdown()
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} is already in use. Try a different port.")
            print(f"💡 You can specify a different port with: python web_server.py --port 3001")
        else:
            print(f"❌ Error starting web server: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Friends League Web Server")
    parser.add_argument("--port", type=int, default=3000, help="Port to run the web server on")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    if args.no_browser:
        # Override the browser opening
        global webbrowser
        webbrowser = None
    
    start_web_server(args.port)


if __name__ == "__main__":
    main()
