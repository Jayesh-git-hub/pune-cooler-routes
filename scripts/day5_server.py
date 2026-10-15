"""
day5_server.py
Lightweight HTTP server providing REST API and serving the Web UI for Pune Cooler Routes.
Supports both Day 5 Dual Routing and Day 6 Multi-Criteria Thermal Comfort Routing.

Endpoints:
  GET /                     -> Serves web/index.html
  GET /style.css            -> Serves web/style.css
  GET /app.js               -> Serves web/app.js
  GET /api/landmarks        -> Returns list of popular Pune landmarks
  GET /api/route            -> Dual-route calculation (start_lat, start_lon, dest_lat, dest_lon, hour, coolness, mode)
  GET /api/benchmark        -> Returns summary of Day 6 25-route benchmark
  GET /api/status           -> Health & network metadata
"""
import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from day5_engine import CoolerRouter, PUNE_LANDMARKS
from day6_router import Day6MultiCriteriaRouter
from config import BBOX, OUTPUTS_DIR

WEB_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "web")
router_v5 = None
router_v6 = None

class CoolerHTTPHandler(BaseHTTPRequestHandler):
    def end_headers(self):
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
                "nodes": len(router_v5.G.nodes) if router_v5 else 0,
                "edges": len(router_v5.G.edges) if router_v5 else 0,
                "day_version": "Day 9 Production (Heatmap + Isochrone + Waypoints)"
            })
        elif path == '/api/route':
            self._handle_route_query(query)
        elif path == '/api/benchmark':
            csv_path = os.path.join(OUTPUTS_DIR, "day6_benchmark_25routes.csv")
            if os.path.exists(csv_path):
                import pandas as pd
                df = pd.read_csv(csv_path)
                self._send_json(df.to_dict(orient='records'))
            else:
                self._send_json({"error": "Benchmark data not yet generated"}, status=404)
        elif path == '/api/shade_score':
            self._handle_shade_score(query)
        elif path == '/api/neighbourhood_scores':
            csv_path = os.path.join(OUTPUTS_DIR, "day8_neighbourhood_scores.csv")
            if os.path.exists(csv_path):
                import pandas as pd
                df = pd.read_csv(csv_path)
                self._send_json(df.to_dict(orient="records"))
            else:
                self._send_json({"error": "Day 8 data not generated yet"}, status=404)
        elif path == '/api/waypoint_recommendations':
            csv_path = os.path.join(OUTPUTS_DIR, "day9_waypoint_recommendations.csv")
            if os.path.exists(csv_path):
                import pandas as pd
                df = pd.read_csv(csv_path)
                self._send_json(df.to_dict(orient="records"))
            else:
                self._send_json({"error": "Day 9 data not generated yet"}, status=404)
        elif path == '/outputs/day9_full_report.html':
            self._serve_file(os.path.join(OUTPUTS_DIR, "day9_full_report.html"), "text/html")
        elif path.startswith('/outputs/') and path.endswith('.geojson'):
            fname = os.path.basename(path)
            fpath = os.path.join(OUTPUTS_DIR, fname)
            if os.path.exists(fpath):
                self._serve_file(fpath, 'application/geo+json')
            else:
                self.send_error(404, f"GeoJSON {fname} not found")
        elif path.startswith('/outputs/') and path.endswith('.png'):
            fname = os.path.basename(path)
            fpath = os.path.join(OUTPUTS_DIR, fname)
            if os.path.exists(fpath):
                self._serve_file(fpath, 'image/png')
            else:
                self.send_error(404, f"PNG {fname} not found")
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

            mode = query.get('mode', ['standard'])[0]

            if not (orig_lat and orig_lon and dest_lat and dest_lon):
                self._send_json({"error": "Missing coordinates"}, status=400)
                return

            if mode in ('balanced', 'multicriteria', 'day6'):
                import datetime
                dt = datetime.datetime.now().replace(hour=hour if hour is not None else 13, minute=0)
                routes_data = router_v6.route(
                    orig_lat=orig_lat, orig_lon=orig_lon,
                    dest_lat=dest_lat, dest_lon=dest_lon,
                    start_dt=dt, w_shade=coolness
                )
            else:
                routes_data = router_v5.compute_dual_routes(
                    orig_lat=orig_lat, orig_lon=orig_lon,
                    dest_lat=dest_lat, dest_lon=dest_lon,
                    hour=hour, coolness_mult=coolness
                )

            if not routes_data:
                self._send_json({"error": "No path exists between coordinates"}, status=404)
                return

            self._send_json(routes_data)

        except Exception as e:
            self._send_json({"error": f"Routing computation failed: {str(e)}"}, status=500)

    def _handle_shade_score(self, query):
        """Return shade score for a clicked lat/lon by finding nearest edge."""
        try:
            lat = float(query.get('lat', [0])[0])
            lon = float(query.get('lon', [0])[0])
            if not (lat and lon):
                self._send_json({"error": "lat/lon required"}, status=400)
                return
            # Find nearest node and lookup shade
            import osmnx as ox
            G = router_v5.G
            node = ox.distance.nearest_nodes(G, X=lon, Y=lat)
            # Get average shade of edges touching this node
            neighbors = list(G.neighbors(node))
            shades = []
            for n in neighbors:
                lookup = router_v5.shade_lookup.get((node, n, 0),
                         router_v5.shade_lookup.get((n, node, 0), {}))
                if lookup:
                    shades.append(lookup.get('1300', 0.25))
            avg = round(sum(shades) / max(1, len(shades)), 4) if shades else 0.25
            self._send_json({
                "lat": lat, "lon": lon,
                "nearest_node": node,
                "shade_1300": round(avg, 4),
                "shade_pct": round(avg * 100, 1),
                "tier": "Deep Canopy" if avg >= 0.60 else
                        "Moderate Shade" if avg >= 0.35 else
                        "Partial Shade" if avg >= 0.15 else "Full Sun"
            })
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

def run_server(port=8050):
    global router_v5, router_v6
    print("Loading Day 5 and Day 6 routing networks...")
    router_v5 = CoolerRouter()
    router_v6 = Day6MultiCriteriaRouter()
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, CoolerHTTPHandler)
    print(f"\n=======================================================")
    print(f" Pune Cooler Routes - Server Live")
    print(f" Port: http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8050
    run_server(port=port)
