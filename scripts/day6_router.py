"""
day6_router.py
Day 6 Advanced Multi-Criteria Routing & Thermal Comfort Engine for Pune Cooler Routes.

Features:
1. Multi-Criteria Cost Function:
   Cost = length * [ 1 + (w_shade * sun_exposure) + (w_safety * road_danger) + (w_sidewalk * sidewalk_quality) ]
2. Thermal Heat Stress Index (THSI):
   Calculates solar irradiance exposure (W/m^2), surface heat absorption, and radiant temperature differential.
3. Time-Marching Simulation:
   Sun angle dynamically shifts along the walk based on real cumulative walking time.
4. Turn-by-Turn Micro-Navigation Guidance:
   Actionable walking advice (e.g. "Stick to north sidewalk under canopy").
"""
import os
import math
import datetime
import networkx as nx
import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
from config import (
    BBOX, PT_MIT_WPU, PT_FC, WALKING_SPEED_KMH,
    DATA_PROCESSED_DIR, OUTPUTS_DIR
)
from day5_engine import PUNE_LANDMARKS

# Walking speed: 4.8 km/h = 80 m/min = 1.333 m/s
WALKING_SPEED_M_MIN = (WALKING_SPEED_KMH * 1000.0) / 60.0

# Pune summer solar irradiance (May/June peak averages in W/m^2)
SOLAR_IRRADIANCE = {
    "0900": 620.0,  # Morning sun
    "1300": 980.0,  # Peak overhead sun
    "1600": 540.0   # Late afternoon angled sun
}

class Day6MultiCriteriaRouter:
    def __init__(self):
        print("Initializing Day 6 Multi-Criteria Routing Engine...")
        self.graphml_path = os.path.join(DATA_PROCESSED_DIR, "network.graphml")
        self.shaded_path = os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg")

        self.G = ox.load_graphml(filepath=self.graphml_path)
        self.nodes_gdf, self.edges_gdf = ox.graph_to_gdfs(self.G)
        self.shaded_gdf = gpd.read_file(self.shaded_path)

        # Lookup table for fast edge attributes
        self.edge_meta = {}
        for _, row in self.shaded_gdf.iterrows():
            k = (int(row['u']), int(row['v']), int(row['key']))
            
            # Sidewalk quality scoring
            # 1.0 = proper footway/sidewalk, 1.5 = unknown/residential, 2.5 = missing on busy arterial
            sw = str(row.get('sidewalk', 'unknown')).lower()
            hw = str(row.get('highway', 'residential')).lower()
            
            if sw in ('yes', 'both', 'left', 'right', 'separate') or 'footway' in hw:
                sw_quality = 1.0
            elif 'residential' in hw or 'living_street' in hw or 'pedestrian' in hw:
                sw_quality = 1.15
            elif 'primary' in hw or 'secondary' in hw or 'trunk' in hw:
                sw_quality = 2.2 # wide road with unverified sidewalk: dangerous
            else:
                sw_quality = 1.4

            # Road safety penalty
            if any(term in hw for term in ('motorway', 'trunk')):
                safety_penalty = 3.5
            elif 'primary' in hw:
                safety_penalty = 1.6
            elif 'secondary' in hw:
                safety_penalty = 1.2
            else:
                safety_penalty = 1.0

            tb = float(row.get('tree_shade_bonus', 0.0) or 0.0)
            self.edge_meta[k] = {
                '0900': min(1.0, float(row.get('shade_frac_0900', 0.25) or 0.25) + tb),
                '1300': min(1.0, float(row.get('shade_frac_1300', 0.15) or 0.15) + tb),
                '1600': min(1.0, float(row.get('shade_frac_1600', 0.30) or 0.30) + tb),
                'tree_bonus': tb,
                'sw_quality': sw_quality,
                'safety_penalty': safety_penalty,
                'surface': str(row.get('surface', 'asphalt')).lower(),
                'highway': hw,
                'name': str(row.get('name', 'Unnamed Street'))
            }

        print(f"Day 6 router ready with {len(self.G.nodes)} nodes and {len(self.edge_meta)} rich edges.")

    def _get_time_slot(self, dt):
        h = dt.hour
        if h < 11:
            return '0900'
        elif h < 15:
            return '1300'
        else:
            return '1600'

    def route(self, orig_lat, orig_lon, dest_lat, dest_lon, start_dt=None,
              w_shade=2.5, w_sidewalk=0.8, w_safety=1.0):
        """
        Computes Fastest, Coolest (Shade-Only), and Multi-Criteria Balanced route.
        """
        if start_dt is None:
            start_dt = datetime.datetime.now().replace(hour=13, minute=0)

        slot = self._get_time_slot(start_dt)
        G_work = self.G.copy()

        # Populate dynamic edge weights
        for u, v, k, data in G_work.edges(keys=True, data=True):
            meta = self.edge_meta.get((u, v, k), self.edge_meta.get((v, u, k), None))
            length = float(data.get('length', 1.0))

            if meta:
                sf = meta[slot]
                sw_penalty = meta['sw_quality']
                safe_mult = meta['safety_penalty']
            else:
                sf = 0.25
                sw_penalty = 1.3
                safe_mult = 1.0

            sun_exposure = max(0.0, 1.0 - sf)
            data['shade_frac'] = sf
            data['raw_length'] = length

            # Pure Shade Cost
            data['shade_cost'] = length * (1.0 + w_shade * sun_exposure) * (safe_mult if safe_mult > 2.0 else 1.0)

            # Balanced Multi-Criteria Cost: Shade + Sidewalk Walkability + Traffic Safety
            data['balanced_cost'] = length * (
                1.0 + 
                (w_shade * sun_exposure) + 
                (w_sidewalk * (sw_penalty - 1.0)) + 
                (w_safety * (safe_mult - 1.0))
            )

        orig_node = ox.distance.nearest_nodes(G_work, X=orig_lon, Y=orig_lat)
        dest_node = ox.distance.nearest_nodes(G_work, X=dest_lon, Y=dest_lat)

        fastest_path = nx.shortest_path(G_work, orig_node, dest_node, weight='length')
        coolest_path = nx.shortest_path(G_work, orig_node, dest_node, weight='shade_cost')
        balanced_path = nx.shortest_path(G_work, orig_node, dest_node, weight='balanced_cost')

        fast_metrics = self._evaluate_route(G_work, fastest_path, "Fastest", start_dt)
        cool_metrics = self._evaluate_route(G_work, coolest_path, "Coolest (Shade Optimized)", start_dt)
        bal_metrics = self._evaluate_route(G_work, balanced_path, "Balanced (Cool & Safe)", start_dt)

        return {
            "start_time": start_dt.strftime("%H:%M"),
            "slot": slot,
            "fastest": fast_metrics,
            "coolest": cool_metrics,
            "balanced": bal_metrics,
            "comparison": {
                "shade_gain_vs_fast": round(cool_metrics['shade_pct'] - fast_metrics['shade_pct'], 1),
                "detour_m_cool": round(cool_metrics['distance_m'] - fast_metrics['distance_m'], 1),
                "detour_min_cool": round(cool_metrics['time_min'] - fast_metrics['time_min'], 1),
                "heat_reduction_w_m2": round(fast_metrics['heat_exposure_w_m2'] - cool_metrics['heat_exposure_w_m2'], 1),
                "thermal_delta_celsius": round(cool_metrics['apparent_temp_relief_c'], 1)
            }
        }

    def _evaluate_route(self, G, path, label, start_dt):
        total_dist = 0.0
        shaded_dist = 0.0
        total_solar_joules = 0.0
        coords = []
        steps = []
        cur_dt = start_dt

        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            d = G[u][v][0]
            seg_len = float(d.get('length', 0.0))
            
            # Dynamic Time-Marching: update time slot based on progress
            seg_time_sec = (seg_len / 1000.0) / WALKING_SPEED_KMH * 3600.0
            cur_dt += datetime.timedelta(seconds=seg_time_sec)
            slot = self._get_time_slot(cur_dt)

            meta = self.edge_meta.get((u, v, 0), self.edge_meta.get((v, u, 0), {}))
            sf = meta.get(slot, d.get('shade_frac', 0.25))

            total_dist += seg_len
            shaded_dist += seg_len * sf

            # Solar radiation received in Watts per m^2
            irradiance = SOLAR_IRRADIANCE.get(slot, 800.0)
            effective_radiation = irradiance * (1.0 - sf * 0.85) # 85% canopy blockage
            total_solar_joules += effective_radiation * seg_time_sec

            u_pt = (self.nodes_gdf.loc[u, 'x'], self.nodes_gdf.loc[u, 'y'])
            v_pt = (self.nodes_gdf.loc[v, 'x'], self.nodes_gdf.loc[v, 'y'])
            if not coords:
                coords.append([u_pt[1], u_pt[0]])
            coords.append([v_pt[1], v_pt[0]])

            name = meta.get('name', 'Unnamed Street')
            hw = meta.get('highway', 'residential')
            steps.append({
                "street": name,
                "length_m": round(seg_len, 1),
                "shade_pct": round(sf * 100.0, 1),
                "is_shaded": sf >= 0.40,
                "advisory": self._generate_advisory(name, sf, hw)
            })

        walk_time_min = (total_dist / 1000.0) / WALKING_SPEED_KMH * 60.0
        shade_pct = (shaded_dist / total_dist * 100.0) if total_dist > 0 else 0.0

        # Mean absorbed solar irradiance
        total_time_sec = walk_time_min * 60.0
        avg_irradiance = (total_solar_joules / total_time_sec) if total_time_sec > 0 else 600.0
        
        # Thermal comfort differential model (approx UTCI radiant depression)
        # 100 W/m^2 solar reduction approximates ~0.9°C to 1.3°C lower radiant heat sensation
        base_sun_irradiance = SOLAR_IRRADIANCE.get(self._get_time_slot(start_dt), 800.0)
        saved_irradiance = max(0.0, base_sun_irradiance - avg_irradiance)
        temp_relief_c = round(saved_irradiance * 0.011, 1)

        # Consolidate steps
        consolidated = []
        for s in steps:
            if not consolidated or consolidated[-1]['street'] != s['street']:
                consolidated.append(dict(s))
            else:
                last = consolidated[-1]
                w_shade = (last['length_m'] * last['shade_pct'] + s['length_m'] * s['shade_pct']) / (last['length_m'] + s['length_m'])
                last['length_m'] = round(last['length_m'] + s['length_m'], 1)
                last['shade_pct'] = round(w_shade, 1)
                last['is_shaded'] = last['shade_pct'] >= 40.0

        return {
            "label": label,
            "distance_m": round(total_dist, 1),
            "time_min": round(walk_time_min, 1),
            "shade_pct": round(shade_pct, 1),
            "heat_exposure_w_m2": round(avg_irradiance, 1),
            "apparent_temp_relief_c": temp_relief_c,
            "coordinates": coords,
            "geojson_coords": [[pt[1], pt[0]] for pt in coords],
            "steps": consolidated
        }

    def _generate_advisory(self, street_name, shade_frac, highway):
        if shade_frac >= 0.60:
            return "Deep continuous tree canopy. Ideal walking corridor."
        elif shade_frac >= 0.40:
            return "Moderate building shadow. Walk on the shaded sidewalk side."
        elif 'primary' in highway or 'trunk' in highway:
            return "Direct sun exposure on wide arterial road. Use umbrella/hat."
        else:
            return "Open street. Cross to shaded building walls where available."

if __name__ == "__main__":
    router = Day6MultiCriteriaRouter()
    res = router.route(
        orig_lat=PT_MIT_WPU[0], orig_lon=PT_MIT_WPU[1],
        dest_lat=PT_FC[0], dest_lon=PT_FC[1],
        start_dt=datetime.datetime(2024, 5, 15, 13, 0)
    )
    print("\n--- Day 6 Multi-Criteria Walk Simulation (MIT-WPU -> FC) ---")
    print(f"Fastest:   {res['fastest']['distance_m']}m  | {res['fastest']['time_min']}m | {res['fastest']['shade_pct']}% shade | Heat: {res['fastest']['heat_exposure_w_m2']} W/m²")
    print(f"Coolest:   {res['coolest']['distance_m']}m  | {res['coolest']['time_min']}m | {res['coolest']['shade_pct']}% shade | Heat: {res['coolest']['heat_exposure_w_m2']} W/m²")
    print(f"Balanced:  {res['balanced']['distance_m']}m  | {res['balanced']['time_min']}m | {res['balanced']['shade_pct']}% shade | Heat: {res['balanced']['heat_exposure_w_m2']} W/m²")
    print(f"Relief:    {res['comparison']['thermal_delta_celsius']}°C apparent temperature drop on Coolest route!")
