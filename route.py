from shapely.geometry import Point
import folium

def calculate_offline_route(graph, start_lat, start_lon, end_lat, end_lon):
    # Find closest graph nodes to start and end points
    nodes, geometries = momepy.nx_to_gdf(graph)
    
    start_point = Point(start_lon, start_lat)
    end_point = Point(end_lon, end_lat)
    
    start_node = nodes.distance(start_point).idxmin()
    end_node = nodes.distance(end_point).idxmin()
    
    # Compute shortest path based on edge length
    path_nodes = nx.shortest_path(graph, source=start_node, target=end_node, weight='length')
    
    # Extract route line geometries
    route_edges = []
    for u, v in zip(path_nodes[:-1], path_nodes[1:]):
        edge_data = graph.get_edge_data(u, v)
        # Take the first key geometry if multigraph
        route_edges.append(list(edge_data.values())[0]['geometry'])
        
    return route_edges

# Example: Calculate route (e.g., Siliguri to Gangtok area)
route_lines = calculate_offline_route(G, 26.7271, 88.3953, 27.3389, 88.6065)

# Render route path on top of your existing Folium map
m = folium.Map(location=[26.71, 88.43], zoom_start=8)
for line in route_lines:
    folium.GeoJson(line, style_function=lambda x: {'color': 'red', 'weight': 4}).add_to(m)

m.save("route_result.html")
print("Route calculated and exported to route_result.html!")