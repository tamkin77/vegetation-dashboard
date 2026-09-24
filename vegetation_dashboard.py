import folium
import geopandas as gpd
import pandas as pd
import branca.colormap as cm

# Load spatial data
areas = gpd.read_file(
    "_11f9096fa2ca482c9f9046a9ed452871_conservation_areas.json"
)

hq = gpd.read_file(
    "_3131a7a4a72a40cdabf0aead071a47d3_hq_points.json"
)

# Load NDVI metrics exported from Google Earth Engine
metrics = pd.read_csv("vegetation_metrics.csv")

# Join metrics with conservation area boundaries
dashboard_data = areas.merge(
    metrics,
    on="area_id",
    how="left",
    validate="one_to_one"
)

# Clean duplicated area-name columns after the join
if "area_name_x" in dashboard_data.columns:
    dashboard_data = dashboard_data.rename(
        columns={"area_name_x": "area_name"}
    )

if "area_name_y" in dashboard_data.columns:
    dashboard_data = dashboard_data.drop(
        columns=["area_name_y"]
    )

# Calculate map center
center = dashboard_data.geometry.union_all().centroid

# Create base map
m = folium.Map(
    location=[center.y, center.x],
    zoom_start=10,
    tiles="OpenStreetMap"
)

# Create diverging color scale for NDVI anomaly
min_anomaly = dashboard_data["anomaly"].min()
max_anomaly = dashboard_data["anomaly"].max()
max_abs = max(abs(min_anomaly), abs(max_anomaly))

colormap = cm.LinearColormap(
    colors=["red", "white", "green"],
    vmin=-max_abs,
    vmax=max_abs
)

colormap.caption = (
    "NDVI anomaly (Current NDVI − 10-year baseline)"
)

# Style conservation areas
def style_function(feature):
    anomaly = feature["properties"]["anomaly"]

    return {
        "fillColor": colormap(anomaly),
        "color": "black",
        "weight": 1.5,
        "fillOpacity": 0.75
    }

# Tooltip
tooltip = folium.GeoJsonTooltip(
    fields=[
        "area_name",
        "current_ndvi",
        "baseline_ndvi",
        "anomaly"
    ],
    aliases=[
        "Conservation area:",
        "Current NDVI:",
        "Baseline NDVI:",
        "Anomaly:"
    ],
    localize=True,
    sticky=False,
    labels=True
)

# Popup
popup = folium.GeoJsonPopup(
    fields=[
        "area_name",
        "current_ndvi",
        "baseline_ndvi",
        "anomaly"
    ],
    aliases=[
        "Conservation area:",
        "Current NDVI:",
        "10-year baseline:",
        "NDVI anomaly:"
    ],
    localize=True,
    labels=True,
    sticky=False
)

# Main conservation area layer
conservation_layer = folium.FeatureGroup(
    name="NDVI Anomaly by Conservation Area",
    show=True
)

folium.GeoJson(
    dashboard_data.to_json(),
    style_function=style_function,
    tooltip=tooltip,
    popup=popup
).add_to(conservation_layer)

conservation_layer.add_to(m)

# Headquarters layer
hq_layer = folium.FeatureGroup(
    name="Headquarters",
    show=True
)

for _, row in hq.iterrows():

    folium.Marker(
        location=[
            row.geometry.y,
            row.geometry.x
        ],
        tooltip=row["area_name"],
        popup=folium.Popup(
            f"""
            <b>Headquarters</b><br>
            Area: {row["area_name"]}<br>
            Area ID: {row["area_id"]}
            """,
            max_width=250
        )
    ).add_to(hq_layer)

hq_layer.add_to(m)

# Add legend
colormap.add_to(m)

# Add title
title_html = """
<div style="
    position: fixed;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    background-color: white;
    padding: 10px 18px;
    border: 2px solid #555;
    border-radius: 5px;
    font-size: 18px;
    font-weight: bold;
    color: #222;
">
Vegetation Dashboard — MODIS NDVI Anomaly
</div>
"""

m.get_root().html.add_child(
    folium.Element(title_html)
)

# Add attribution
attribution_html = """
<div style="
    position: fixed;
    bottom: 5px;
    left: 5px;
    z-index: 9999;
    background-color: rgba(255,255,255,0.9);
    padding: 5px 8px;
    font-size: 10px;
">
NDVI: MODIS MOD13Q1 via Google Earth Engine |
Boundaries: provided conservation area dataset
</div>
"""

m.get_root().html.add_child(
    folium.Element(attribution_html)
)

# Add layer control
folium.LayerControl(
    collapsed=False
).add_to(m)

# Save dashboard
m.save("vegetation_dashboard.html")

print("Dashboard created successfully!")
print("File: vegetation_dashboard.html")