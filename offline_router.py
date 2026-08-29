import osmnx as ox
import folium

# 1. Load the graph directly from your local PBF file
# Note: Ensure you have gdal / pyosmium installed for XML/PBF parsing in OSMnx
print("Loading OSM PBF data into graph...")
G = ox.graph_from_xml("ne_full.osm.pbf", network_type="drive")

# 2. Convert the road network graph to GeoDataFrames (nodes and edges)
nodes, edges = ox.graph_to_gdfs(G)

# 3. Create a Folium Map centered on the region (e.g., North East / Siliguri area)
center_lat, center_lon = 26.71, 88.43
m = folium.Map(location=[center_lat, center_lon], zoom_start=8, tiles="cartodbpositron")

# 4. Plot the road network edges directly onto the interactive map canvas
folium.GeoJson(
    edges[['geometry', 'name', 'highway']],
    style_function=lambda x: {'color': '#3388ff', 'weight': 1.5, 'opacity': 0.7},
    tooltip=folium.GeoJsonTooltip(fields=['name', 'highway'], aliases=['Road Name:', 'Type:'])
).add_to(m)

# 5. Save locally as an offline HTML viewer
m.save("map.html")
print("Map successfully exported to map.html!")