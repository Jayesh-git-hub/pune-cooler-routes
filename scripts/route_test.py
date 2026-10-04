import os
import osmnx as ox
import networkx as nx
import random
import geopandas as gpd
from shapely.geometry import Point, LineString
from config import PT_MIT_WPU, PT_FC, WALKING_SPEED_KMH, DATA_PROCESSED_DIR, OUTPUTS_DIR

def main():
    print("Loading network...")
    G = ox.load_graphml(filepath=os.path.join(DATA_PROCESSED_DIR, "network.graphml"))
    
    print("\nVerifying test points by geocoding...")
    try:
        mit_geo = ox.geocode("MIT-WPU, Kothrud, Pune")
        dist_mit = ox.distance.great_circle(PT_MIT_WPU[0], PT_MIT_WPU[1], mit_geo[0], mit_geo[1])
        print(f"MIT-WPU geocode differs by {dist_mit:.1f} m from user coordinates.")
        if dist_mit > 300:
            print("WARNING: MIT-WPU differs by more than 300 m!")
    except Exception as e:
        print(f"MIT-WPU geocode failed: {e}")
        
    try:
        fc_geo = ox.geocode("Fergusson College, Pune")
        dist_fc = ox.distance.great_circle(PT_FC[0], PT_FC[1], fc_geo[0], fc_geo[1])
        print(f"Fergusson College geocode differs by {dist_fc:.1f} m from user coordinates.")
        if dist_fc > 300:
            print("WARNING: Fergusson College differs by more than 300 m!")
    except Exception as e:
        print(f"Fergusson College geocode failed: {e}")

    print("\nSnapping points to nearest network nodes...")
    u = ox.distance.nearest_nodes(G, X=PT_MIT_WPU[1], Y=PT_MIT_WPU[0], return_dist=True)
    v = ox.distance.nearest_nodes(G, X=PT_FC[1], Y=PT_FC[0], return_dist=True)
    
    orig_node, orig_dist = u
    dest_node, dest_dist = v
    print(f"MIT-WPU snapped distance: {orig_dist:.1f} m")
    print(f"Fergusson College snapped distance: {dest_dist:.1f} m")

    print("\nCalculating shortest walking route...")
    try:
        route = nx.shortest_path(G, orig_node, dest_node, weight='length')
        
        route_dist_m = sum(G[u][v][0]['length'] for u, v in zip(route[:-1], route[1:]))
        route_time_h = (route_dist_m / 1000) / WALKING_SPEED_KMH
        route_time_m = route_time_h * 60
        num_segments = len(route) - 1
        
        print(f"Route distance: {route_dist_m:.1f} m")
        print(f"Walking time: {route_time_m:.1f} minutes")
        print(f"Number of segments: {num_segments}")
        
        names = []
        for u_node, v_node in zip(route[:-1], route[1:]):
            edge = G[u_node][v_node][0]
            name = edge.get('name', 'Unnamed')
            if isinstance(name, list):
                name = ", ".join(name)
            names.append(name)
            
        dedup_names = []
        for name in names:
            if not dedup_names or name != dedup_names[-1]:
                dedup_names.append(name)
        
        print(f"Street names in order: {', '.join(dedup_names)}")
        
        fig, ax = ox.plot_graph_route(G, route, show=False, save=True, filepath=os.path.join(OUTPUTS_DIR, "route_test.png"))
        
        nodes, edges = ox.graph_to_gdfs(G)
        route_nodes = nodes.loc[route]
        line = LineString(route_nodes['geometry'].tolist())
        route_gdf = gpd.GeoDataFrame({'id': [1]}, geometry=[line], crs=G.graph['crs'])
        route_gdf.to_file(os.path.join(OUTPUTS_DIR, "route_test.geojson"), driver="GeoJSON")
        print("Saved route plot and GeoJSON.")
        
    except nx.NetworkXNoPath:
        print("No route found between the points.")

    print("\nTesting 20 random node pairs...")
    nodes_list = list(G.nodes())
    success_count = 0
    random.seed(42)
    for _ in range(20):
        n1 = random.choice(nodes_list)
        n2 = random.choice(nodes_list)
        try:
            nx.shortest_path(G, n1, n2, weight='length')
            success_count += 1
        except nx.NetworkXNoPath:
            pass
            
    print(f"{success_count} out of 20 random routes succeeded.")

if __name__ == "__main__":
    main()
