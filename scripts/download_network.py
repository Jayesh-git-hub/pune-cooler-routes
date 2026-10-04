import os
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box

from config import BBOX, DATA_PROCESSED_DIR, OUTPUTS_DIR

def main():
    print("Configuring OSMnx...")
    useful_tags = ox.settings.useful_tags_way
    new_tags = ['sidewalk', 'sidewalk:left', 'sidewalk:right', 'sidewalk:both', 
                'footway', 'crossing', 'surface', 'lit', 'covered', 'layer', 'indoor']
    
    for tag in new_tags:
        if tag not in useful_tags:
            useful_tags.append(tag)
    ox.settings.useful_tags_way = useful_tags

    print(f"Downloading network for bbox {BBOX}...")
    G = ox.graph_from_bbox(bbox=BBOX, network_type="walk", simplify=True, retain_all=True)
    
    print("Saving pilot box to geojson...")
    polygon = box(BBOX[0], BBOX[1], BBOX[2], BBOX[3])
    gdf_box = gpd.GeoDataFrame({'id': [1]}, geometry=[polygon], crs="EPSG:4326")
    gdf_box.to_file(os.path.join(OUTPUTS_DIR, "pilot_box.geojson"), driver="GeoJSON")

    nodes, edges = ox.graph_to_gdfs(G)
    
    print(f"Initial network: {len(nodes)} nodes, {len(edges)} edges")
    total_length_m = edges['length'].sum()
    print(f"Total length: {total_length_m / 1000:.2f} km")
    
    print("\nEdge counts by highway type:")
    if 'highway' in edges.columns:
        highway_counts = edges['highway'].astype(str).value_counts()
        for hw, count in highway_counts.items():
            print(f"{hw}: {count}")

    print("\nExtracting largest connected component...")
    import networkx as nx
    largest_scc = max(nx.strongly_connected_components(G), key=len)
    G_lcc = G.subgraph(largest_scc).copy()
    nodes_dropped = len(G.nodes) - len(G_lcc.nodes)
    print(f"Dropped {nodes_dropped} nodes not in the largest connected component.")
    
    print("Saving graph and edges...")
    ox.save_graphml(G_lcc, filepath=os.path.join(DATA_PROCESSED_DIR, "network.graphml"))
    
    nodes_lcc, edges_lcc = ox.graph_to_gdfs(G_lcc)
    
    # GPKG does not support list types
    for col in edges_lcc.columns:
        if any(isinstance(val, list) for val in edges_lcc[col]):
            edges_lcc[col] = edges_lcc[col].astype(str)
            
    edges_lcc.to_file(os.path.join(DATA_PROCESSED_DIR, "edges.gpkg"), layer="edges", driver="GPKG")
    
    print("Plotting network...")
    fig, ax = ox.plot_graph(G_lcc, show=False, save=True, filepath=os.path.join(OUTPUTS_DIR, "network.png"))
    print("Network download step completed!")

if __name__ == "__main__":
    main()
