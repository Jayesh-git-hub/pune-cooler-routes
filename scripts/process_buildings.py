import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from config import DATA_PROCESSED_DIR, PT_MIT_WPU, PT_FC

def main():
    raw_path = os.path.join(DATA_PROCESSED_DIR, "buildings_raw.geojson")
    if not os.path.exists(raw_path):
        print(f"File not found: {raw_path}")
        return
        
    print("Loading raw buildings from GeoJSON...")
    buildings = gpd.read_file(raw_path)
    
    print("Cleaning data and assigning default heights...")
    if 'mean' in buildings.columns:
        buildings = buildings.rename(columns={'mean': 'height'})
        
    if 'height' not in buildings.columns:
        buildings['height'] = None
        
    no_height_mask = buildings['height'].isna()
    buildings.loc[no_height_mask, 'height'] = 6.0
    buildings['is_default_height'] = no_height_mask
    
    print(f"Total buildings: {len(buildings)}")
    print(f"Buildings with default height: {no_height_mask.sum()}")
    
    out_gpkg = os.path.join(DATA_PROCESSED_DIR, "buildings.gpkg")
    buildings.to_file(out_gpkg, driver="GPKG")
    print(f"Saved cleaned buildings to {out_gpkg}")
    
    print("\nReality Check (20 buildings near MIT-WPU & FC):")
    mit = Point(PT_MIT_WPU[1], PT_MIT_WPU[0])
    fc = Point(PT_FC[1], PT_FC[0])
    
    near_mit = buildings[buildings.geometry.intersects(mit.buffer(0.002))].head(10)
    near_fc = buildings[buildings.geometry.intersects(fc.buffer(0.002))].head(10)
    
    test_buildings = pd.concat([near_mit, near_fc])
    for idx, row in test_buildings.iterrows():
        h = row['height']
        d = row['is_default_height']
        print(f"Building ID {idx}: Height = {h:.1f} m (Default: {d})")

if __name__ == "__main__":
    main()
