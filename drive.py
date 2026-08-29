# offline_router.py
from pyrosm import OSM
import folium

# Initialize OSM parser with merged dataset
osm = OSM("ne_full.osm.pbf")

# Extract driving network
drive_net = osm.get_network(network_type="driving")

# Render interactively
m = drive_net.explore(column="highway", cmap="tab10")
m.save("ne_map.html")

print("Saved map to ne_map.html. Open it in any browser!")