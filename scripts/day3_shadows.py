import os
import geopandas as gpd
import pandas as pd
import osmnx as ox
import pybdshadow
import datetime
from config import BBOX, DATA_PROCESSED_DIR

def get_buildings_and_trees():
    print("Downloading buildings and trees from OSMnx...")
    west, south, east, north = BBOX
    bbox = BBOX
    
    ox.settings.timeout = 180
    
    print("Fetching buildings...")
    buildings = ox.features.features_from_bbox(bbox=bbox, tags={'building': True})
    buildings = buildings.to_crs("EPSG:4326")
    buildings = buildings[buildings.geometry.type.isin(['Polygon', 'MultiPolygon'])]
    
    def clean_height(x):
        try:
            if isinstance(x, str): x = x.replace('m', '').replace(' ', '')
            return float(x)
        except:
            return 6.0
            
    buildings['height'] = buildings['height'].apply(clean_height)
    buildings = buildings[['geometry', 'height']].copy()
    
    print("Fetching trees (Solving Loophole 1: Missing Trees)...")
    try:
        trees = ox.features.features_from_bbox(bbox=bbox, tags={'natural': ['tree', 'tree_row', 'wood']})
        trees = trees.to_crs("EPSG:4326")
        
        trees_proj = trees.to_crs(buildings.estimate_utm_crs())
        trees_proj['geometry'] = trees_proj.geometry.buffer(5.0)
        trees_wgs = trees_proj.to_crs("EPSG:4326")
        trees_wgs['height'] = 10.0
        trees_wgs = trees_wgs[['geometry', 'height']].copy()
        
        combined = pd.concat([buildings, trees_wgs], ignore_index=True)
        combined = gpd.GeoDataFrame(combined, geometry='geometry', crs="EPSG:4326")
        combined['building_id'] = range(len(combined))
        print(f"Loaded {len(buildings)} buildings and {len(trees_wgs)} trees.")
    except Exception as e:
        print("Could not load trees:", e)
        combined = buildings
        
    return combined

def calculate_shadows(combined, edges):
    print("Calculating shadows for different times (Solving Loophole 4: Dynamic Times)...")
    # Datetimes in UTC. India is UTC+5:30.
    times = [
        ("0900", datetime.datetime(2024, 5, 15, 9, 0)),
        ("1300", datetime.datetime(2024, 5, 15, 13, 0)),
        ("1600", datetime.datetime(2024, 5, 15, 16, 0))
    ]
    
    edges_proj = edges.to_crs(combined.estimate_utm_crs())
    
    for label, dt in times:
        print(f"Processing time {label}...")
        shadows = pybdshadow.bdshadow_sunlight(combined, dt, height='height')
        shadows.set_crs("EPSG:4326", allow_override=True, inplace=True)
        shadows_proj = shadows.to_crs(edges_proj.crs)
        
        print(f"Intersecting {len(shadows_proj)} shadows with {len(edges_proj)} edges using spatial join...")
        joined = gpd.sjoin(edges_proj[['geometry']], shadows_proj[['geometry']], how='left', predicate='intersects')
        
        shade_lengths = {}
        for edge_idx, group in joined.groupby(joined.index):
            if pd.isna(group['index_right'].iloc[0]):
                shade_lengths[edge_idx] = 0.0
                continue
            
            edge_geom = edges_proj.loc[edge_idx, 'geometry']
            shd_geoms = shadows_proj.loc[group['index_right'], 'geometry']
            
            if hasattr(shd_geoms, 'union_all'):
                shd_union = shd_geoms.union_all()
            else:
                shd_union = shd_geoms.unary_union
                
            intersection = edge_geom.intersection(shd_union)
            shade_lengths[edge_idx] = intersection.length
            
        edge_lengths = edges_proj.geometry.length
        shade_series = pd.Series(shade_lengths)
        edges_proj[f'shade_frac_{label}'] = (shade_series / edge_lengths).fillna(0.0).clip(0, 1.0)
        
    print("Applying Covered Walkways logic (Solving Loophole 5)...")
    if 'covered' in edges_proj.columns:
        covered_mask = edges_proj['covered'] == 'yes'
        for label, _ in times:
            edges_proj.loc[covered_mask, f'shade_frac_{label}'] = 1.0
            
    edges_final = edges_proj.to_crs(edges.crs)
    return edges_final

def main():
    combined = get_buildings_and_trees()
    
    edges_path = os.path.join(DATA_PROCESSED_DIR, "edges.gpkg")
    if not os.path.exists(edges_path):
        print(f"Edges not found at {edges_path}")
        return
        
    edges = gpd.read_file(edges_path)
    
    edges_shaded = calculate_shadows(combined, edges)
    
    out_path = os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg")
    
    for col in edges_shaded.columns:
        if edges_shaded[col].apply(lambda x: isinstance(x, (list, dict))).any():
            edges_shaded[col] = edges_shaded[col].astype(str)
            
    edges_shaded.to_file(out_path, driver="GPKG")
    print(f"Saved shaded edges to {out_path}")

if __name__ == "__main__":
    main()
