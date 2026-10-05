import os
import osmnx as ox
import geopandas as gpd
from config import BBOX, DATA_PROCESSED_DIR

def main():
    print("Downloading buildings from OSMnx (Fallback for Google Earth Engine)...")
    # In OSMnx 2.x, bbox is (west, south, east, north)
    buildings = ox.features.features_from_bbox(bbox=BBOX, tags={'building': True})
    
    # We need to project the geometries to EPSG:4326 if not already
    buildings = buildings.to_crs("EPSG:4326")
    
    if 'height' not in buildings.columns:
        buildings['height'] = None
        
    def clean_height(x):
        try:
            # some heights might be '12 m'
            if isinstance(x, str):
                x = x.replace('m', '').replace(' ', '')
            return float(x)
        except:
            return None
            
    buildings['height'] = buildings['height'].apply(clean_height)
    
    # Handle lists/dicts which break GeoJSON export
    for col in buildings.columns:
        if buildings[col].apply(lambda x: isinstance(x, (list, dict))).any():
            buildings[col] = buildings[col].astype(str)
            
    out_path = os.path.join(DATA_PROCESSED_DIR, "buildings_raw.geojson")
    # Drop rows without geometry
    buildings = buildings.dropna(subset=['geometry'])
    # GeoJSON doesn't support geometry collections well, keep only polygons
    buildings = buildings[buildings.geometry.type.isin(['Polygon', 'MultiPolygon'])]
    
    buildings.to_file(out_path, driver="GeoJSON")
    print(f"Saved {len(buildings)} OSM buildings to {out_path}")

if __name__ == "__main__":
    main()
