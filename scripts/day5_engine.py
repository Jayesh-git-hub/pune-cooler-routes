"""
day5_engine.py
Core dual-routing engine for Day 5 interactive web app.
Supports:
- Arbitrary (lat, lon) start and destination anywhere in the Pune pilot box
- Dynamic time-of-day shade selection (09:00, 13:00, 16:00, or live hour)
- Adjustable coolness slider (shade weight multiplier)
- Turn-by-turn walking directions with shade status
- GeoJSON export ready for Leaflet map display
"""
import os
import datetime
import networkx as nx
import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point, mapping
from config import (
    BBOX, PT_MIT_WPU, PT_FC, WALKING_SPEED_KMH,
    DATA_PROCESSED_DIR, OUTPUTS_DIR
)

# Pune Pilot Landmarks for quick-routing
PUNE_LANDMARKS = {
    "mit_wpu": {"name": "MIT-WPU Campus, Kothrud", "lat": 18.5178, "lon": 73.8151},
    "fergusson": {"name": "Fergusson College, FC Road", "lat": 18.5236, "lon": 73.8408},
    "deccan": {"name": "Deccan Gymkhana", "lat": 18.5172, "lon": 73.8415},
    "bmcc": {"name": "BMCC (Brihan Maharashtra College of Commerce)", "lat": 18.5218, "lon": 73.8340},
    "ils_law": {"name": "ILS Law College, Law College Rd", "lat": 18.5165, "lon": 73.8268},
    "sambhaji_park": {"name": "Chhatrapati Sambhaji Garden", "lat": 18.5192, "lon": 73.8471},
    "kamla_nehru": {"name": "Kamla Nehru Park, Prabhat Rd", "lat": 18.5118, "lon": 73.8336},
    "garware": {"name": "MES Garware College, Karve Rd", "lat": 18.5085, "lon": 73.8342},
    "fc_market": {"name": "FC Road Shopping Street", "lat": 18.5262, "lon": 73.8419}
}

class CoolerRouter:
    def __init__(self):
        print("Initializing CoolerRouter...")
        self.graphml_path = os.path.join(DATA_PROCESSED_DIR, "network.graphml")
        self.shaded_path = os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg")
        
        # Load base graph
        self.G = ox.load_graphml(filepath=self.graphml_path)
        self.nodes_gdf, self.edges_gdf = ox.graph_to_gdfs(self.G)
        
        # Load shaded edges table
        self.shaded_gdf = gpd.read_file(self.shaded_path)
        
        # Build quick edge shade lookup: (u, v, key) -> dict of shade columns
        self.shade_lookup = {}
        for _, row in self.shaded_gdf.iterrows():
            k = (int(row['u']), int(row['v']), int(row['key']))
            tb = float(row.get('tree_shade_bonus', 0.0) or 0.0)
            self.shade_lookup[k] = {
                '0900': min(1.0, float(row.get('shade_frac_0900', 0.0) or 0.0) + tb),
                '1300': min(1.0, float(row.get('shade_frac_1300', 0.0) or 0.0) + tb),
                '1600': min(1.0, float(row.get('shade_frac_1600', 0.0) or 0.0) + tb),
                'tree_bonus': tb,
                'sidewalk': str(row.get('sidewalk', 'unknown')),
                'highway': str(row.get('highway', 'residential'))
            }
        print(f"Router ready with {len(self.G.nodes)} nodes and {len(self.shade_lookup)} shaded edges.")

    def get_shade_key(self, hour):
        if hour is None:
            hour = datetime.datetime.now().hour
        if hour < 11:
            return '0900', 'shade_frac_0900'
        elif hour < 15:
            return '1300', 'shade_frac_1300'
        else:
            return '1600', 'shade_frac_1600'

    def prepare_weighted_graph(self, hour=None, coolness_mult=2.5):
        """Prepares edge weights based on selected hour and coolness multiplier."""
        key_label, col_name = self.get_shade_key(hour)
        G_weighted = self.G.copy()

        for u, v, k, data in G_weighted.edges(keys=True, data=True):
            lookup_val = self.shade_lookup.get((u, v, k), self.shade_lookup.get((v, u, k), None))
            sf = lookup_val[key_label] if lookup_val else 0.25
            data['shade_frac'] = sf
            
            # Sun fraction: 1.0 = fully exposed, 0.0 = fully shaded
            sun_frac = max(0.0, 1.0 - sf)
            length = data.get('length', 1.0)
            
            # Cool weight: base length inflated by exposure to scorching sun
            cool_w = length * (1.0 + coolness_mult * sun_frac)
            
            # Road safety penalty: motorway/trunk dangerous for pedestrians
            hw = data.get('highway', '')
            if isinstance(hw, list):
                hw = hw[0] if hw else ''
            if hw in ('motorway', 'trunk', 'motorway_link', 'trunk_link'):
                cool_w *= 3.0
            
            data['cool_weight'] = cool_w
            
        return G_weighted, key_label

    def compute_dual_routes(self, orig_lat, orig_lon, dest_lat, dest_lon, hour=None, coolness_mult=2.5):
        """Computes both Fastest and Coolest walking routes between two points."""
        G_w, key_label = self.prepare_weighted_graph(hour=hour, coolness_mult=coolness_mult)
        
        # Snap coordinates to nearest graph nodes
        orig_node = ox.distance.nearest_nodes(G_w, X=orig_lon, Y=orig_lat)
        dest_node = ox.distance.nearest_nodes(G_w, X=dest_lon, Y=dest_lat)
        
        # 1. Fastest Route (Dijkstra on physical distance)
        try:
            fastest_path = nx.shortest_path(G_w, orig_node, dest_node, weight='length')
        except nx.NetworkXNoPath:
            return None
            
        # 2. Coolest Route (Dijkstra on shade-weighted cost)
        try:
            coolest_path = nx.shortest_path(G_w, orig_node, dest_node, weight='cool_weight')
        except nx.NetworkXNoPath:
            coolest_path = fastest_path

        fastest_details = self._extract_path_details(G_w, fastest_path, 'Fastest')
        coolest_details = self._extract_path_details(G_w, coolest_path, 'Coolest')

        # Tradeoff calculations
        extra_dist = round(coolest_details['distance_m'] - fastest_details['distance_m'], 1)
        extra_time = round(coolest_details['time_min'] - fastest_details['time_min'], 1)
        shade_gain = round(coolest_details['shade_pct'] - fastest_details['shade_pct'], 1)

        result = {
            "query": {
                "origin": {"lat": orig_lat, "lon": orig_lon},
                "destination": {"lat": dest_lat, "lon": dest_lon},
                "hour_slot": key_label,
                "coolness_multiplier": coolness_mult
            },
            "tradeoff": {
                "extra_distance_m": max(0.0, extra_dist),
                "extra_time_min": max(0.0, extra_time),
                "shade_gain_pct": shade_gain,
                "verdict": self._format_verdict(extra_dist, extra_time, shade_gain)
            },
            "fastest": fastest_details,
            "coolest": coolest_details
        }
        return result

    def _extract_path_details(self, G, path, label):
        """Extracts geometry, steps, distances and shade fractions for a path."""
        coords = []
        steps = []
        total_len = 0.0
        shaded_len = 0.0

        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            edge_data = G[u][v][0]
            
            u_pt = (self.nodes_gdf.loc[u, 'x'], self.nodes_gdf.loc[u, 'y'])
            v_pt = (self.nodes_gdf.loc[v, 'x'], self.nodes_gdf.loc[v, 'y'])
            if not coords:
                coords.append([u_pt[1], u_pt[0]])
            coords.append([v_pt[1], v_pt[0]])

            seg_len = float(edge_data.get('length', 0.0))
            sf = float(edge_data.get('shade_frac', 0.0) or 0.0)
            total_len += seg_len
            shaded_len += seg_len * sf

            # Street name
            name = edge_data.get('name', 'Unnamed Street')
            if isinstance(name, list):
                name = ', '.join(name)
                
            steps.append({
                "street": name,
                "length_m": round(seg_len, 1),
                "shade_pct": round(sf * 100, 1),
                "is_shaded": sf >= 0.40
            })

        # Consolidate consecutive steps with identical street name
        consolidated_steps = []
        for s in steps:
            if not consolidated_steps or consolidated_steps[-1]['street'] != s['street']:
                consolidated_steps.append(dict(s))
            else:
                last = consolidated_steps[-1]
                weighted_shade = (last['length_m'] * last['shade_pct'] + s['length_m'] * s['shade_pct']) / (last['length_m'] + s['length_m'])
                last['length_m'] = round(last['length_m'] + s['length_m'], 1)
                last['shade_pct'] = round(weighted_shade, 1)
                last['is_shaded'] = last['shade_pct'] >= 40.0

        time_min = (total_len / 1000.0) / WALKING_SPEED_KMH * 60.0
        shade_pct = (shaded_len / total_len * 100.0) if total_len > 0 else 0.0

        # GeoJSON LineString geometry: [[lon, lat], ...]
        geojson_coords = [[pt[1], pt[0]] for pt in coords]

        return {
            "label": label,
            "distance_m": round(total_len, 1),
            "time_min": round(time_min, 1),
            "shade_pct": round(shade_pct, 1),
            "shaded_meters": round(shaded_len, 1),
            "sunny_meters": round(max(0.0, total_len - shaded_len), 1),
            "coordinates": coords,          # Leaflet [lat, lon]
            "geojson_coords": geojson_coords,# GeoJSON [lon, lat]
            "steps": consolidated_steps
        }

    def _format_verdict(self, extra_dist, extra_time, shade_gain):
        if shade_gain <= 0.5:
            return "Both routes share similar tree canopy corridors."
        elif shade_gain < 5.0:
            return f"Coolest route gains +{shade_gain}% shade with only +{extra_time} min walking detour."
        else:
            return f"Significant heat reduction! +{shade_gain}% more tree shade for just +{extra_time} min (+{extra_dist}m)."

if __name__ == "__main__":
    router = CoolerRouter()
    res = router.compute_dual_routes(
        orig_lat=PT_MIT_WPU[0], orig_lon=PT_MIT_WPU[1],
        dest_lat=PT_FC[0], dest_lon=PT_FC[1],
        hour=13, coolness_mult=2.5
    )
    print("\n--- TEST ROUTE: MIT-WPU to Fergusson College (13:00) ---")
    print(f"Fastest: {res['fastest']['distance_m']} m | {res['fastest']['time_min']} min | {res['fastest']['shade_pct']}% shade")
    print(f"Coolest: {res['coolest']['distance_m']} m | {res['coolest']['time_min']} min | {res['coolest']['shade_pct']}% shade")
    print(f"Tradeoff: {res['tradeoff']['verdict']}")
