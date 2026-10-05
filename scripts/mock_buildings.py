import geopandas as gpd
from shapely.geometry import Polygon, Point
import os
from config import DATA_PROCESSED_DIR, PT_MIT_WPU, PT_FC

def main():
    print("Overpass API is down. Generating mock building footprints to unblock Day 3...")
    mit = Point(PT_MIT_WPU[1], PT_MIT_WPU[0])
    fc = Point(PT_FC[1], PT_FC[0])
    
    polys = []
    for pt in [mit, fc]:
        for i in range(10):
            offset = i * 0.0002
            poly = Polygon([
                (pt.x + offset, pt.y + offset),
                (pt.x + offset + 0.0001, pt.y + offset),
                (pt.x + offset + 0.0001, pt.y + offset + 0.0001),
                (pt.x + offset, pt.y + offset + 0.0001)
            ])
            polys.append(poly)
            
    gdf = gpd.GeoDataFrame({'geometry': polys, 'height': [6.0]*20, 'is_default_height': [True]*20}, crs="EPSG:4326")
    
    out_gpkg = os.path.join(DATA_PROCESSED_DIR, "buildings.gpkg")
    gdf.to_file(out_gpkg, driver="GPKG")
    print(f"Saved {len(gdf)} mock buildings to {out_gpkg}")

if __name__ == "__main__":
    main()
