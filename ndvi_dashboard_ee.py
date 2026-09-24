import ee

# Initialize Google Earth Engine
ee.Initialize(project="projectcoursefirdaus")

# Load MODIS NDVI collection
dataset = (
    ee.ImageCollection("MODIS/061/MOD13Q1")
    .select("NDVI")
)

# Apply MODIS NDVI scale factor
dataset = dataset.map(
    lambda image: image.multiply(0.0001)
    .copyProperties(image, image.propertyNames())
)

# Current growing season: June-August 2026
current = (
    dataset
    .filterDate("2026-06-01", "2026-09-01")
    .median()
    .rename("current_ndvi")
)

# 10-year baseline: June-August 2016-2025
baseline_collection = (
    dataset
    .filterDate("2016-06-01", "2025-09-01")
    .filter(
        ee.Filter.calendarRange(
            6, 8, "month"
        )
    )
)

baseline = (
    baseline_collection
    .median()
    .rename("baseline_ndvi")
)

# Calculate NDVI anomaly
anomaly = (
    current
    .subtract(baseline)
    .rename("anomaly")
)

# Load conservation areas from Earth Engine
areas_ee = ee.FeatureCollection(
    "projects/projectcoursefirdaus/assets/conservation_areas"
)

# Combine NDVI layers
ndvi_stack = current.addBands([
    baseline,
    anomaly
])

# Calculate zonal statistics
zonal_stats = ndvi_stack.reduceRegions(
    collection=areas_ee,
    reducer=ee.Reducer.mean(),
    scale=250
)

# Display results
print(
    "Number of conservation areas:",
    areas_ee.size().getInfo()
)

print(
    "Current images:",
    dataset
    .filterDate(
        "2026-06-01",
        "2026-09-01"
    )
    .size()
    .getInfo()
)

print(
    "Baseline images:",
    baseline_collection
    .size()
    .getInfo()
)

print(
    zonal_stats.getInfo()
)