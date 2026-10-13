"""
day5_server.py
Lightweight HTTP server providing REST API and serving the Web UI for Pune Cooler Routes.
Endpoints:
  GET /                     -> Serves web/index.html
  GET /style.css            -> Serves web/style.css
  GET /app.js               -> Serves web/app.js
  GET /api/landmarks        -> Returns list of popular Pune landmarks
  GET /api/route            -> Dual-route calculation (start_lat, start_lon, dest_lat, dest_lon, hour, coolness)
  GET /api/status           -> Health & network metadata
"""
import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add scripts directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from day5_engine import CoolerRouter, PUNE_LANDMARKS
from config import BBOX

WEB_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "web")
router_instance = None

class CoolerHTTPHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for local testing
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path in ('/', '/index.html'):
            self._serve_file(os.path.join(WEB_DIR, 'index.html'), 'text/html')
        elif path == '/style.css':
            self._serve_file(os.path.join(WEB_DIR, 'style.css'), 'text/css')
        elif path == '/app.js':
            self._serve_file(os.path.join(WEB_DIR, 'app.js'), 'application/javascript')
        elif path == '/api/landmarks':
            self._send_json(PUNE_LANDMARKS)
        elif path == '/api/status':
            self._send_json({
                "status": "online",
                "city": "Pune, Maharashtra, India",
                "pilot_bbox": BBOX,
                "landmarks_count": len(PUNE_LANDMARKS),
                "nodes": len(router_instance.G.nodes) if router_instance else 0,
                "edges": len(router_instance.G.edges) if router_instance else 0
            })
        elif path == '/api/route':
            self._handle_route_query(query)
        else:
            self.send_error(404, "File not found")

    def _serve_file(self, file_path, content_type):
        if not os.path.exists(file_path):
            self.send_error(404, f"File {file_path} not found")
            return
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

    def _send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_route_query(self, query):
        try:
            orig_lat = float(query.get('start_lat', [0])[0])
            orig_lon = float(query.get('start_lon', [0])[0])
            dest_lat = float(query.get('dest_lat', [0])[0])
            dest_lon = float(query.get('dest_lon', [0])[0])
            
            hour_str = query.get('hour', [None])[0]
            hour = int(hour_str) if (hour_str and hour_str.isdigit()) else None
            
            cool_str = query.get('coolness', ['2.5'])[0]
            coolness = float(cool_str) if cool_str else 2.5

            if not (orig_lat and orig_lon and dest_lat and dest_lon):
                self._send_json({"error": "Missing start_lat, start_lon, dest_lat, or dest_lon"}, status=400)
                return

            routes_data = router_instance.compute_dual_routes(
                orig_lat=orig_lat, orig_lon=orig_lon,
                dest_lat=dest_lat, dest_lon=dest_lon,
                hour=hour, coolness_mult=coolness
            )

            if not routes_data:
                self._send_json({"error": "No route could be found between specified locations"}, status=404)
                return

            self._send_json(routes_data)

        except Exception as e:
            self._send_json({"error": f"Route computation failed: {str(e)}"}, status=500)

def run_server(port=8050):
    global router_instance
    print("Loading graph network & shade models into memory...")
    router_instance = CoolerRouter()
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, CoolerHTTPHandler)
    print(f"\n=======================================================")
    print(f" Pune Cooler Routes - Day 5 Web Application Server")
    print(f" Live at: http://127.0.0.1:{port}")
    print(f" REST API: http://127.0.0.1:{port}/api/route")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8050
    run_server(port=port)
