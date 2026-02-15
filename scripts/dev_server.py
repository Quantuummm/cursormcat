"""
Simple dev server for MCAT Mastery frontend.
Serves the repo root so frontend/ can access ../lore/ via fetch.

Usage:
    python scripts/dev_server.py [port]
    
Default port: 8080
Open: http://localhost:8080/frontend/
"""

import http.server
import socketserver
import sys
import os
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
REPO_ROOT = Path(__file__).resolve().parents[1]

os.chdir(REPO_ROOT)

class CORSHandler(http.server.SimpleHTTPRequestHandler):
    """Allow CORS and serve JSON with correct MIME type."""
    
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        '.json': 'application/json',
        '.js':   'application/javascript',
        '.mjs':  'application/javascript',
        '.woff2': 'font/woff2',
        '.webp': 'image/webp',
        '.webmanifest': 'application/manifest+json',
    }
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Compact logging
        if args and '200' in str(args):
            return  # Skip 200s for cleaner output
        super().log_message(format, *args)

with socketserver.TCPServer(("", PORT), CORSHandler) as httpd:
    print(f"\n🌐 MCAT Mastery Dev Server")
    print(f"   Serving: {REPO_ROOT}")
    print(f"   Open:    http://localhost:{PORT}/frontend/")
    print(f"   Press Ctrl+C to stop\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
