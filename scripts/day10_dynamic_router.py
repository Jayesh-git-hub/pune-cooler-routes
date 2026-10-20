"""
day10_dynamic_router.py
Day 10: Dynamic Time-Varying Solar Routing & Walkability Safety Engine.

Addresses Key Architectural Loopholes:
1. Dynamic Sun-Marching: Solar shade changes continuously as pedestrian walks (time-varying sun angle).
2. Continuous Solar Irradiance: Estimates real-time solar radiation absorbed (kJ) along the route.
3. Sidewalk Infrastructure & Safety Weighting: Penalizes roads with missing sidewalks or heavy vehicle traffic.
4. Micro-Navigation Guidance: Turn-by-turn steps with specific sidewalk side advisories (e.g. West vs East curb).

Outputs / APIs:
- Day10DynamicRouter class for routing calculations
- CLI test runner demonstrating dynamic vs static route differences
"""
import os
import sys
import math
import datetime
import networkx as nx
import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from config import (
    BBOX, WALKING_SPEED_KMH, DATA_PROCESSED_DIR, OUTPUTS_DIR
)
from day5_engine import PUNE_LANDMARKS

# Walking speed: 4.8 km/h = 80 m/min = 1.333 m/s
WALKING_SPEED_M_MIN = (WALKING_SPEED_KMH * 1000.0) / 60.0
WALKING_SPEED_M_S = WALKING_SPEED_M_MIN / 60.0

# Cycling speed: 15.0 km/h = 250 m/min = 4.167 m/s
CYCLING_SPEED_KMH = 15.0
CYCLING_SPEED_M_MIN = (CYCLING_SPEED_KMH * 1000.0) / 60.0
CYCLING_SPEED_M_S = CYCLING_SPEED_M_MIN / 60.0

# Human projected surface area under direct sun (~0.6 m^2 for standing/walking human)
HUMAN_EXPOSED_AREA_M2 = 0.60


def get_solar_irradiance_at_hour(hour_float: float) -> float:
    """
    Returns estimated clear-sky global horizontal irradiance (W/m^2) for Pune in May.
    Peaks at ~980 W/m^2 at 13:00.
    """
    if hour_float < 6.0 or hour_float > 18.5:
        return 0.0
    # Solar zenith approximation (cosine bell curve peaking at 13:00)
    solar_time_diff = abs(hour_float - 13.0)
    if solar_time_diff > 6.0:
        return 0.0
    norm_factor = math.cos((solar_time_diff / 6.0) * (math.pi / 2.0))
    return round(980.0 * (norm_factor ** 1.3), 1)


class Day10DynamicRouter:
    """
    Dynamic time-aware routing engine that marches the sun position forward
    as the user walks along street segments.
    """
    def __init__(self):
        print("Initializing Day 10 Dynamic Time-Varying Router...")
        self.graphml_path = os.path.join(DATA_PROCESSED_DIR, "network.graphml")
        self.shaded_path = os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg")

        self.G = ox.load_graphml(filepath=self.graphml_path)
        self.shaded_gdf = gpd.read_file(self.shaded_path)

        # Build fast lookup dictionary for edges
        self.edge_meta = {}
        for _, row in self.shaded_gdf.iterrows():
            k = (int(row['u']), int(row['v']), int(row['key']))
            
            # Sidewalk infrastructure quality score (1.0 = best, 2.5 = worst)
            sw = str(row.get('sidewalk', 'unknown')).lower()
            hw = str(row.get('highway', 'residential')).lower()
            
            if sw in ('yes', 'both', 'separate') or 'footway' in hw:
                sw_quality = 1.0
                sw_desc = "Dedicated sidewalk"
            elif sw in ('left', 'right') or 'pedestrian' in hw or 'living_street' in hw:
                sw_quality = 1.15
                sw_desc = "One-side sidewalk / pedestrian zone"
            elif 'residential' in hw:
                sw_quality = 1.25
                sw_desc = "Calm residential street"
            elif 'primary' in hw or 'trunk' in hw:
                sw_quality = 2.40  # Busy arterial with unverified pedestrian path
                sw_desc = "High-speed road (caution)"
            elif 'secondary' in hw:
                sw_quality = 1.70
                sw_desc = "Secondary collector road"
            else:
                sw_quality = 1.35
                sw_desc = "Standard urban roadway"

            # Traffic safety penalty multiplier
            if any(term in hw for term in ('motorway', 'trunk')):
                safety_penalty = 3.5
            elif 'primary' in hw:
                safety_penalty = 1.65
            elif 'secondary' in hw:
                safety_penalty = 1.25
            else:
                safety_penalty = 1.0

            tb = float(row.get('tree_shade_bonus', 0.0) or 0.0)
            s09 = min(1.0, float(row.get('shade_frac_0900', 0.25) or 0.25) + tb)
            s13 = min(1.0, float(row.get('shade_frac_1300', 0.15) or 0.15) + tb)
            s16 = min(1.0, float(row.get('shade_frac_1600', 0.30) or 0.30) + tb)

            self.edge_meta[k] = {
                's0900': s09,
                's1300': s13,
                's1600': s16,
                'tree_bonus': tb,
                'sw_quality': sw_quality,
                'sw_desc': sw_desc,
                'safety_penalty': safety_penalty,
                'highway': hw,
                'name': str(row.get('name', 'Unnamed Street'))
            }

        print(f"Day 10 router loaded {len(self.G.nodes)} nodes & {len(self.edge_meta)} edges.")

    def get_interpolated_shade(self, u: int, v: int, k: int, hour_float: float) -> float:
        """
        Calculates time-continuous shade fraction for edge (u, v, k) at any floating hour (e.g. 13.45).
        Interpolates piecewise smoothly between 09:00, 13:00, and 16:00.
        """
        meta = self.edge_meta.get((u, v, k), self.edge_meta.get((v, u, k), None))
        if not meta:
            return 0.25
        
        s09 = meta['s0900']
        s13 = meta['s1300']
        s16 = meta['s1600']

        if hour_float <= 9.0:
            return s09
        elif hour_float >= 16.0:
            return s16
        elif 9.0 < hour_float <= 13.0:
            # Morning to midday interpolation
            t = (hour_float - 9.0) / 4.0
            return (1.0 - t) * s09 + t * s13
        else:
            # Midday to afternoon interpolation
            t = (hour_float - 13.0) / 3.0
            return (1.0 - t) * s13 + t * s16

    def _generate_turn_guidance(self, route_nodes: list, departure_dt: datetime.datetime, speed_m_s: float = WALKING_SPEED_M_S, travel_mode: str = 'walk'):
        """
        Produces detailed turn-by-turn navigation instructions with micro-navigation
        sidewalk side advisories and real-time sun angles.
        """
        steps = []
        cum_dist = 0.0
        cum_seconds = 0.0
        curr_dt = departure_dt

        for i in range(len(route_nodes) - 1):
            u = route_nodes[i]
            v = route_nodes[i + 1]
            
            # Retrieve edge data
            edge_dict = self.G.get_edge_data(u, v, 0) or {}
            length = float(edge_dict.get('length', 50.0))
            name = str(edge_dict.get('name', 'Connecting Street'))
            if name == 'nan' or not name:
                name = 'Connecting Street'

            # Advance dynamic time for this segment
            transit_sec = length / speed_m_s
            hour_float = curr_dt.hour + (curr_dt.minute / 60.0) + (curr_dt.second / 3600.0)
            
            shade = self.get_interpolated_shade(u, v, 0, hour_float)
            meta = self.edge_meta.get((u, v, 0), self.edge_meta.get((v, u, 0), {}))
            tree_bonus = meta.get('tree_bonus', 0.0)
            sw_desc = meta.get('sw_desc', 'Paved path')

            # Determine sidewalk shade recommendation
            # In Northern Hemisphere, morning sun is in East -> West side shaded; afternoon sun in West -> East side shaded
            if hour_float < 12.0:
                side_advice = "Stick to West / South sidewalk for building shadow"
            elif 12.0 <= hour_float <= 14.5:
                if tree_bonus > 0.05:
                    side_advice = "Walk under continuous tree canopy corridor"
                else:
                    side_advice = "Center overhead sun: pick shaded shop awnings"
            else:
                side_advice = "Stick to East / North sidewalk for deep afternoon shadows"

            # Compute compass bearing
            u_y, u_x = self.G.nodes[u]['y'], self.G.nodes[u]['x']
            v_y, v_x = self.G.nodes[v]['y'], self.G.nodes[v]['x']
            dy = v_y - u_y
            dx = (v_x - u_x) * math.cos(math.radians(u_y))
            bearing = (math.degrees(math.atan2(dx, dy)) + 360.0) % 360.0

            compass = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int((bearing + 22.5) // 45) % 8]

            steps.append({
                "step_index": i + 1,
                "street": name,
                "distance_m": round(length, 1),
                "duration_s": round(transit_sec, 0),
                "clock_time": curr_dt.strftime("%H:%M:%S"),
                "shade_pct": round(shade * 100.0, 1),
                "compass": compass,
                "infrastructure": sw_desc,
                "advisory": side_advice,
                "solar_irradiance_w": get_solar_irradiance_at_hour(hour_float)
            })

            cum_dist += length
            cum_seconds += transit_sec
            curr_dt += datetime.timedelta(seconds=transit_sec)

        return steps

    def route(self, orig_lat: float, orig_lon: float, dest_lat: float, dest_lon: float,
              departure_time_str: str = "12:30", w_shade: float = 2.8, w_safety: float = 1.3,
              travel_mode: str = "walk"):
        """
        Computes 3 routes:
        1. Fastest (length-only)
        2. Static Coolest (fixed noon sun)
        3. Dynamic Time-Varying Safe & Cool (time-marching solar angle + sidewalk safety)
        """
        orig_node = ox.distance.nearest_nodes(self.G, X=orig_lon, Y=orig_lat)
        dest_node = ox.distance.nearest_nodes(self.G, X=dest_lon, Y=dest_lat)

        if orig_node == dest_node:
            return None

        # Parse departure time
        h, m = [int(x) for x in departure_time_str.split(":")]
        departure_dt = datetime.datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
        dep_hour_float = h + (m / 60.0)

        if travel_mode == "bicycle":
            speed_m_s = CYCLING_SPEED_M_S
        elif travel_mode == "max_cool":
            speed_m_s = WALKING_SPEED_M_S
            w_shade = max(w_shade, 6.0)
        else:
            speed_m_s = WALKING_SPEED_M_S

        G_work = self.G.copy()

        # 1. Populate weights
        for u, v, k, data in G_work.edges(keys=True, data=True):
            length = float(data.get('length', 1.0))
            meta = self.edge_meta.get((u, v, k), self.edge_meta.get((v, u, k), None))

            # Static noon shade
            static_shade = meta['s1300'] if meta else 0.25
            sw_quality = meta['sw_quality'] if meta else 1.3
            safety_mult = meta['safety_penalty'] if meta else 1.0

            # Dynamic shade at departure time
            dyn_shade = self.get_interpolated_shade(u, v, k, dep_hour_float)

            # Weight assignments
            data['weight_fastest'] = length
            data['weight_static_cool'] = length * (1.0 + w_shade * (1.0 - static_shade))
            
            # Day 10 Dynamic + Safe weight (pedestrian vs cycling)
            if travel_mode == "bicycle":
                hw = meta['highway'] if meta else ''
                if any(x in hw for x in ('steps', 'footway', 'pedestrian', 'corridor')):
                    cycle_penalty = 4.0
                elif any(x in hw for x in ('motorway', 'trunk')):
                    cycle_penalty = 5.0
                elif any(x in hw for x in ('residential', 'secondary', 'tertiary', 'living_street')):
                    cycle_penalty = 0.8
                else:
                    cycle_penalty = 1.1
                data['weight_dynamic_safe'] = length * (
                    1.0 +
                    w_shade * (1.0 - dyn_shade) +
                    cycle_penalty * 0.4
                )
            else:
                data['weight_dynamic_safe'] = length * (
                    1.0 +
                    w_shade * (1.0 - dyn_shade) +
                    w_safety * (sw_quality - 1.0) * safety_mult
                )

        # Compute paths
        try:
            path_fastest = nx.shortest_path(G_work, orig_node, dest_node, weight='weight_fastest')
            path_static = nx.shortest_path(G_work, orig_node, dest_node, weight='weight_static_cool')
            path_dynamic = nx.shortest_path(G_work, orig_node, dest_node, weight='weight_dynamic_safe')
        except nx.NetworkXNoPath:
            return None

        # Summarize each path
        routes = {}
        for mode_key, path in [('fastest', path_fastest), ('static_coolest', path_static), ('dynamic_safe_cool', path_dynamic)]:
            coords = []
            total_dist = 0.0
            total_time_s = 0.0
            weighted_shade_sum = 0.0
            total_solar_joules = 0.0
            sidewalk_score_sum = 0.0
            curr_dt = departure_dt

            for i in range(len(path) - 1):
                u_curr = path[i]
                v_curr = path[i + 1]
                edge_data = G_work.get_edge_data(u_curr, v_curr, 0) or {}
                l = float(edge_data.get('length', 1.0))
                dt_step = l / speed_m_s
                
                t_hour = curr_dt.hour + (curr_dt.minute / 60.0) + (curr_dt.second / 3600.0)
                sh = self.get_interpolated_shade(u_curr, v_curr, 0, t_hour)
                irr = get_solar_irradiance_at_hour(t_hour)

                # Solar energy absorbed (Joules = Watts * seconds * area)
                sun_frac = max(0.0, 1.0 - sh)
                solar_joules = irr * sun_frac * dt_step * HUMAN_EXPOSED_AREA_M2
                total_solar_joules += solar_joules

                meta = self.edge_meta.get((u_curr, v_curr, 0), self.edge_meta.get((v_curr, u_curr, 0), {}))
                sw_q = meta.get('sw_quality', 1.3)
                sidewalk_score_sum += (1.0 / sw_q) * l

                total_dist += l
                total_time_s += dt_step
                weighted_shade_sum += sh * l
                curr_dt += datetime.timedelta(seconds=dt_step)

            # Extract polyline lat/lon
            for node_id in path:
                nd = self.G.nodes[node_id]
                coords.append([round(nd['y'], 6), round(nd['x'], 6)])

            mean_shade = weighted_shade_sum / max(1.0, total_dist)
            walkability_idx = round((sidewalk_score_sum / max(1.0, total_dist)) * 100.0, 1)

            routes[mode_key] = {
                "distance_m": round(total_dist, 1),
                "duration_min": round(total_time_s / 60.0, 1),
                "duration_s": round(total_time_s, 0),
                "mean_shade_pct": round(mean_shade * 100.0, 1),
                "solar_energy_kj": round(total_solar_joules / 1000.0, 1),
                "walkability_score": walkability_idx,
                "coordinates": coords,
                "arrival_time": curr_dt.strftime("%H:%M")
            }

        # Turn guidance for the chosen coolest route
        chosen_path = path_static if (travel_mode == "max_cool" or routes['static_coolest']['mean_shade_pct'] >= routes['dynamic_safe_cool']['mean_shade_pct']) else path_dynamic
        steps = self._generate_turn_guidance(chosen_path, departure_dt, speed_m_s=speed_m_s, travel_mode=travel_mode)

        # Comparative analysis
        solar_avoided_kj = round(routes['fastest']['solar_energy_kj'] - routes['dynamic_safe_cool']['solar_energy_kj'], 1)
        shade_gain_pct = round(routes['dynamic_safe_cool']['mean_shade_pct'] - routes['fastest']['mean_shade_pct'], 1)
        detour_m = round(routes['dynamic_safe_cool']['distance_m'] - routes['fastest']['distance_m'], 1)
        detour_min = round(routes['dynamic_safe_cool']['duration_min'] - routes['fastest']['duration_min'], 1)

        return {
            "travel_mode": travel_mode,
            "speed_kmh": CYCLING_SPEED_KMH if travel_mode == "bicycle" else WALKING_SPEED_KMH,
            "departure_time": departure_time_str,
            "fastest": routes['fastest'],
            "static_coolest": routes['static_coolest'],
            "dynamic_safe_cool": routes['dynamic_safe_cool'],
            "tradeoff": {
                "detour_m": detour_m,
                "detour_min": detour_min,
                "shade_gain_pct": shade_gain_pct,
                "solar_avoided_kj": solar_avoided_kj,
                "walkability_improvement": round(routes['dynamic_safe_cool']['walkability_score'] - routes['fastest']['walkability_score'], 1)
            },
            "steps": steps
        }


if __name__ == "__main__":
    router = Day10DynamicRouter()
    o = PUNE_LANDMARKS["mit_wpu"]
    d = PUNE_LANDMARKS["fergusson"]
    res = router.route(o["lat"], o["lon"], d["lat"], d["lon"], departure_time_str="13:00")
    print("\n================== DAY 10 ROUTING TEST ==================")
    print(f"Departure: 13:00 (MIT-WPU -> Fergusson College)")
    print(f"Fastest:            {res['fastest']['distance_m']}m | {res['fastest']['duration_min']}min | {res['fastest']['mean_shade_pct']}% shade | {res['fastest']['solar_energy_kj']} kJ")
    print(f"Dynamic Safe+Cool:  {res['dynamic_safe_cool']['distance_m']}m | {res['dynamic_safe_cool']['duration_min']}min | {res['dynamic_safe_cool']['mean_shade_pct']}% shade | {res['dynamic_safe_cool']['solar_energy_kj']} kJ")
    print(f"Tradeoff:           +{res['tradeoff']['detour_m']}m ({res['tradeoff']['detour_min']}min) | +{res['tradeoff']['shade_gain_pct']}% shade | Avoided {res['tradeoff']['solar_avoided_kj']} kJ solar heat")
    print(f"Walkability Score:  {res['dynamic_safe_cool']['walkability_score']}/100 vs {res['fastest']['walkability_score']}/100")
    print(f"Total Turn Steps:   {len(res['steps'])}")
    print("========================================================\n")
