import os
import osmnx as ox
import geopandas as gpd
import pandas as pd
import ast
import matplotlib.pyplot as plt

from config import DATA_PROCESSED_DIR, OUTPUTS_DIR

def parse_val(v):
    if isinstance(v, list):
        return [str(x).lower() for x in v]
    if isinstance(v, str):
        if v.startswith('[') and v.endswith(']'):
            try:
                l = ast.literal_eval(v)
                return [str(x).lower() for x in l]
            except:
                return [v.lower()]
        return [v.lower()]
    return []

def check_sidewalk_tags(row):
    keys = ['sidewalk', 'sidewalk:left', 'sidewalk:right', 'sidewalk:both']
    has_positive = False
    has_negative = False
    
    for key in keys:
        if key in row and pd.notna(row[key]):
            vals = parse_val(row[key])
            for v in vals:
                if v in ['yes', 'both', 'left', 'right', 'separate']:
                    has_positive = True
                elif v in ['no', 'none']:
                    has_negative = True
                    
    if has_positive:
        return 'sidewalk tagged'
    if has_negative:
        return 'no sidewalk tagged'
    return 'untagged'

def is_motor(highway_val):
    motor_types = ['primary', 'secondary', 'tertiary', 'unclassified', 'residential', 'living_street']
    vals = parse_val(highway_val)
    return any(v in motor_types for v in vals)

def is_footway(highway_val):
    foot_types = ['footway', 'pedestrian']
    vals = parse_val(highway_val)
    return any(v in foot_types for v in vals)
    
def is_main_road(highway_val):
    main_types = ['primary', 'secondary', 'tertiary']
    vals = parse_val(highway_val)
    return any(v in main_types for v in vals)

def main():
    print("Loading edges from geopackage...")
    edges = gpd.read_file(os.path.join(DATA_PROCESSED_DIR, "edges.gpkg"))
    
    print("Filtering motor roads and footways...")
    motor_mask = edges['highway'].apply(is_motor)
    foot_mask = edges['highway'].apply(is_footway)
    
    edges_motor = edges[motor_mask].copy()
    edges_footway = edges[foot_mask].copy()
    
    print("Projecting to local CRS for distance measurements...")
    edges_motor_proj = ox.projection.project_gdf(edges_motor)
    edges_footway_proj = ox.projection.project_gdf(edges_footway)
    
    print("Buffering footways by 15m...")
    footway_buffered = edges_footway_proj.geometry.buffer(15).unary_union
    
    print("Categorizing motor segments...")
    categories = []
    for idx, row in edges_motor_proj.iterrows():
        tag_status = check_sidewalk_tags(row)
        if tag_status == 'sidewalk tagged':
            categories.append('sidewalk tagged')
        elif tag_status == 'no sidewalk tagged':
            categories.append('no sidewalk tagged')
        else:
            # Check intersection
            geom = row['geometry']
            intersection = geom.intersection(footway_buffered)
            if intersection.length >= 0.5 * geom.length:
                categories.append('footway nearby')
            else:
                categories.append('unknown')
                
    edges_motor['category'] = categories
    edges_motor_proj['category'] = categories
    
    # Calculate lengths in km
    edges_motor_proj['length_km'] = edges_motor_proj.geometry.length / 1000.0
    
    print("\nSummary Table (All motor roads):")
    summary_all = edges_motor_proj.groupby('category')['length_km'].agg(['count', 'sum']).rename(columns={'count': 'segments', 'sum': 'km'})
    print(summary_all)
    
    print("\nSummary Table (Primary/Secondary/Tertiary only):")
    main_mask = edges_motor_proj['highway'].apply(is_main_road)
    summary_main = edges_motor_proj[main_mask].groupby('category')['length_km'].agg(['count', 'sum']).rename(columns={'count': 'segments', 'sum': 'km'})
    print(summary_main)
    
    # Gaps for top 25
    print("\nExtracting top 25 gaps...")
    gaps = edges_motor_proj[edges_motor_proj['category'] == 'unknown'].copy()
    
    def format_name(row):
        name = row.get('name', None)
        hw = str(row['highway'])
        if pd.isna(name) or name == '':
            return f"unnamed (highway={hw})"
        if isinstance(name, list) or (isinstance(name, str) and name.startswith('[')):
            vals = parse_val(name)
            return ", ".join(vals)
        return str(name)

    gaps['display_name'] = gaps.apply(format_name, axis=1)
    gaps['is_main'] = gaps['highway'].apply(is_main_road)
    
    # Group by name and highway
    # But wait, highway might be a list representation. Let's just group by display_name and the raw highway string
    gap_groups = gaps.groupby(['display_name', 'highway', 'is_main'])['length_km'].sum().reset_index()
    
    # Sort: main roads first, then by length descending
    gap_groups = gap_groups.sort_values(by=['is_main', 'length_km'], ascending=[False, False])
    
    top25 = gap_groups.head(25).drop(columns=['is_main'])
    top25.to_csv(os.path.join(OUTPUTS_DIR, "sidewalk_gaps_top25.csv"), index=False)
    print("Saved top 25 gaps to csv.")
    
    # Plotting
    print("Plotting sidewalk audit map...")
    color_map = {
        'sidewalk tagged': 'blue',
        'footway nearby': 'green',
        'no sidewalk tagged': 'red',
        'unknown': 'orange'
    }
    
    fig, ax = plt.subplots(figsize=(10, 10))
    # Plot background
    edges.plot(ax=ax, color='lightgray', linewidth=0.5, alpha=0.5)
    
    for cat, color in color_map.items():
        subset = edges_motor[edges_motor['category'] == cat]
        if not subset.empty:
            subset.plot(ax=ax, color=color, linewidth=1.5, label=cat)
            
    plt.legend()
    plt.title("Sidewalk Audit")
    plt.axis('off')
    plt.savefig(os.path.join(OUTPUTS_DIR, "sidewalk_audit.png"), dpi=300, bbox_inches='tight')
    print("Saved sidewalk audit map.")
    print("Audit completed!")

if __name__ == "__main__":
    main()
