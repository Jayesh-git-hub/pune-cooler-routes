import ee
import os
import requests
import geopandas as gpd
from config import BBOX, DATA_PROCESSED_DIR

def authenticate():
    try:
        ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')
    except Exception as e:
        print("Earth Engine is not initialized.")
        print("Please run 'earthengine authenticate' in your terminal.")
        raise e

def main():
    authenticate()
    west, south, east, north = BBOX
    region = ee.Geometry.BBox(west, south, east, north)
    
    print("Loading Google Open Buildings V3 footprints...")
    buildings_fc = ee.FeatureCollection("GOOGLE/Research/open-buildings/v3/polygons") \
        .filterBounds(region)
        
    print("Loading 2.5D Temporal heights...")
    temporal_25d = ee.ImageCollection("GOOGLE/Research/open-buildings-2point5d/v1") \
        .filterBounds(region) \
        .mosaic()
        
    height_band = temporal_25d.select('height')
    confidence_band = temporal_25d.select('confidence')
    
    valid_height = height_band.updateMask(confidence_band.gte(0.6))
    
    print("Joining heights to building footprints using zonal statistics...")
    buildings_with_height = valid_height.reduceRegions(
        collection=buildings_fc,
        reducer=ee.Reducer.mean(),
        scale=4,
        crs='EPSG:4326'
    )
    
    print("Exporting data via download URL...")
    url = buildings_with_height.getDownloadURL(filetype='geojson')
    response = requests.get(url)
    
    out_path = os.path.join(DATA_PROCESSED_DIR, "buildings_raw.geojson")
    with open(out_path, "wb") as f:
        f.write(response.content)
        
    print(f"Downloaded {out_path} successfully.")

if __name__ == "__main__":
    main()
