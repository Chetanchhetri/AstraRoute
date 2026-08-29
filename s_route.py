import geopandas as gpd
import networkx as nx
from shapely.geometry import Point
from sklearn.neighbors import KDTree
from math import radians, cos, sin, asin, sqrt
import folium

def haversine(lon1, lat1, lon2, lat2):
    # Calculate distance in km between two geo coordinates
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r

print("Loading merged road dataset...")
gdf = gpd.read_file("ne_combined_roads.gpkg")

# Filter major drivable roads
highways = gdf[gdf['highway'].notnull()].copy()
major_roads = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential']
highways = highways[highways['highway'].isin(major_roads)]

print("Building graph...")
G = nx.Graph()

for idx, row in highways.iterrows():
    geom = row['geometry']
    if geom.geom_type == 'LineString':
        coords = list(geom.coords)
        for i in range(len(coords) - 1):
            u, v = coords[i], coords[i+1]
            # u and v are (lon, lat) tuples
            dist_km = haversine(u[0], u[1], v[0], v[1])
            G.add_edge(u, v, weight=dist_km)

print("Filtering largest connected road network...")
largest_cc = max(nx.connected_components(G), key=len)
G_sub = G.subgraph(largest_cc).copy()

# Build spatial query index
node_coords = list(G_sub.nodes())
kdtree = KDTree(node_coords)

def get_accurate_route(graph, start_lon, start_lat, end_lon, end_lat):
    # Find exact nearest road nodes
    _, start_idx = kdtree.query([[start_lon, start_lat]], k=1)
    _, end_idx = kdtree.query([[end_lon, end_lat]], k=1)
    
    start_node = node_coords[start_idx[0][0]]
    end_node = node_coords[end_idx[0][0]]
    
    path = nx.shortest_path(graph, source=start_node, target=end_node, weight='weight')
    
    # Calculate total path distance
    total_km = sum(graph[u][v]['weight'] for u, v in zip(path[:-1], path[1:]))
    return path, total_km

# Coordinates: Siliguri (88.4353, 26.7271) to Gangtok (88.6138, 27.3389)
print("Calculating route from Siliguri to Gangtok...")
route_points, distance = get_accurate_route(G_sub, 88.4353, 26.7271, 88.6138, 27.3389)
print(f"Calculated Route Distance: {distance:.2f} km")

# Render Map
m = folium.Map(location=[27.0, 88.5], zoom_start=9)
folium.PolyLine([(lat, lon) for lon, lat in route_points], color="blue", weight=5, opacity=0.8).add_to(m)

# Add Start and End Markers
folium.Marker([26.7271, 88.4353], popup="Siliguri", icon=folium.Icon(color="green")).add_to(m)
folium.Marker([27.3389, 88.6138], popup="Gangtok", icon=folium.Icon(color="red")).add_to(m)

m.save("offline_route.html")
print("Corrected route saved to offline_route.html!")