"""
fix_shade_fracs.py
Uses pre-saved buildings.gpkg to skip the 9000+ OSMnx subqueries.
"""
import os
import osmnx as ox
import geopandas as gpd
import pandas as pd
import pybdshadow
import datetime
from config import BBOX, DATA_PROCESSED_DIR, DATA_CACHE_DIR

ox.settings.use_cache = True
ox.settings.cache_folder = DATA_CACHE_DIR
ox.settings.max_query_area_size = 10000000000

TIMES = {
    "0900": datetime.datetime(2024, 5, 15, 9, 0),
    "1300": datetime.datetime(2024, 5, 15, 13, 0),
    "1600": datetime.datetime(2024, 5, 15, 16, 0),
}

def get_combined():
    print("Loading buildings from buildings.gpkg...")
    buildings_path = os.path.join(DATA_PROCESSED_DIR, "buildings.gpkg")
    buildings = gpd.read_file(buildings_path)
    buildings = buildings.to_crs("EPSG:4326")
    
    def clean_h(x):
        try:
            if isinstance(x, str): x = x.replace('m','').strip()
            return float(x)
        except: return 6.0
    
    if 'height' not in buildings.columns:
        buildings['height'] = 6.0
    else:
        buildings['height'] = buildings['height'].apply(clean_h)
        
    buildings = buildings[['geometry', 'height']].copy()

    # Trees only takes ~50 queries because there are fewer trees, but let's just 
    # disable trees if we want it to be instant. Or fetch trees with ox if we want.
    print("Fetching trees (only a few queries needed for trees)...")
    try:
        west, south, east, north = BBOX
        bbox = BBOX
        trees = ox.features.features_from_bbox(bbox=bbox, tags={'natural': ['tree','tree_row','wood']})
        trees = trees.to_crs("EPSG:4326")
        utm = buildings.estimate_utm_crs()
        tp = trees.to_crs(utm); tp['geometry'] = tp.geometry.buffer(5.0)
        tw = tp.to_crs("EPSG:4326"); tw['height'] = 10.0
        combined = pd.concat([buildings, tw[['geometry','height']]], ignore_index=True)
    except Exception as e:
        print(f"Trees skipped: {e}"); combined = buildings

    combined = gpd.GeoDataFrame(combined, geometry='geometry', crs="EPSG:4326")
    combined['building_id'] = range(len(combined))
    print(f"Combined: {len(combined)} features")
    return combined

def fix_edges(combined):
    edges_path = os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg")
    edges = gpd.read_file(edges_path)
    utm = combined.estimate_utm_crs()
    edges_proj = edges.to_crs(utm).copy()

    for label, dt in TIMES.items():
        col = f"shade_frac_{label}"
        print(f"\nProcessing {label}...")
        shadows = pybdshadow.bdshadow_sunlight(combined, dt, height='height')
        shadows.set_crs("EPSG:4326", allow_override=True, inplace=True)
        shadows_proj = shadows.to_crs(utm)

        joined = gpd.sjoin(
            edges_proj[['u','v','key','geometry']].reset_index(drop=True),
            shadows_proj[['geometry']].reset_index(drop=True),
            how='left', predicate='intersects'
        )

        shade_vals = []
        for i, edge_row in edges_proj.iterrows():
            hits = joined[(joined['u']==edge_row['u']) &
                          (joined['v']==edge_row['v']) &
                          (joined['key']==edge_row['key']) &
                          joined['index_right'].notna()]
            if hits.empty:
                shade_vals.append(0.0)
                continue
            shadow_ids = hits['index_right'].astype(int).unique()
            valid_ids = [sid for sid in shadow_ids if sid < len(shadows_proj)]
            if not valid_ids:
                shade_vals.append(0.0)
                continue
            shd_union = shadows_proj.iloc[valid_ids]['geometry'].union_all()
            inter = edge_row['geometry'].intersection(shd_union)
            elen = edge_row['geometry'].length
            shade_vals.append(inter.length / elen if elen > 0 else 0.0)

        edges_proj[col] = shade_vals
        non_zero = (edges_proj[col] > 0).sum()
        print(f"  {non_zero}/{len(edges_proj)} edges have shade > 0")

    edges_fixed = edges_proj.to_crs("EPSG:4326")
    for c in edges_fixed.columns:
        if edges_fixed[c].apply(lambda x: isinstance(x, (list,dict))).any():
            edges_fixed[c] = edges_fixed[c].astype(str)
    out = os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg")
    edges_fixed.to_file(out, driver="GPKG")
    print(f"\nSaved fixed edges to {out}")

if __name__ == "__main__":
    combined = get_combined()
    fix_edges(combined)
    print("Done!")
