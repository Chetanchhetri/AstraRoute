import pyogrio
import geopandas as gpd
import pandas as pd

print("Loading Eastern Zone...")
gdf_east = gpd.read_file("eastern-zone-260826.osm.pbf", layer="lines", engine="pyogrio")

print("Loading North-Eastern Zone...")
gdf_ne = gpd.read_file("north-eastern-zone-260826.osm.pbf", layer="lines", engine="pyogrio")

# Combine both datasets
print("Merging datasets...")
merged_gdf = pd.concat([gdf_east, gdf_ne], ignore_index=True)
merged_gdf = gpd.GeoDataFrame(merged_gdf, crs=gdf_east.crs)

# Save to a single GeoPackage file for fast reading
merged_gdf.to_file("ne_combined_roads.gpkg", driver="GPKG")
print("Saved combined network to ne_combined_roads.gpkg!")