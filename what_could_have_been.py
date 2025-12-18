#!/usr/bin/env python3

import geopandas as gpd
import pandas as pd
import requests
from io import BytesIO
from pathlib import Path

# ============================================================
# URLs — official public ArcGIS REST endpoints
# ============================================================

SF_PARCELS_URL = (
    "https://sfplanninggis.org/arcgiswa/rest/services/"
    "PlanningData/MapServer/23/query"
    "?where=1=1&outFields=*&returnGeometry=true&f=geojson"
)

SF_ZONING_URL = (
    "https://sfplanninggis.org/arcgiswa/rest/services/"
    "PlanningData/MapServer/3/query"
    "?where=1=1&outFields=*&returnGeometry=true&f=geojson"
)

SF_HEIGHT_URL = (
    "https://sfplanninggis.org/arcgiswa/rest/services/"
    "PlanningData/MapServer/5/query"
    "?where=1=1&outFields=*&returnGeometry=true&f=geojson"
)

# Historic constraint layers (union these for exclusion/low feasibility)
# NOTE: Layer 71 (nsr_historic) is "No Significant Resource" - properties that are NOT historic!
#       We exclude it from this list.
HISTORIC_LAYERS = {
    "historic_resources": 0,
    "landmarks": 11,
    "article10_districts": 17,
    "article11_districts": 16,
    "national_register": 6,
    "california_register": 7,
    "historic_survey": 30,
    # "nsr_historic": 71,  # REMOVED - this is "No Significant Resource" (approved non-historic)
}

# Slope layers
SLOPE_LAYERS = {
    "slope_20_25": 18,
    "slope_25_plus": 19,
}

# Open space
OPEN_SPACE_LAYER = 20

def make_planning_url(layer_id):
    return (
        f"https://sfplanninggis.org/arcgiswa/rest/services/"
        f"PlanningData/MapServer/{layer_id}/query"
        f"?where=1=1&outFields=*&returnGeometry=true&f=geojson"
)

SB79_URL = (
    "https://services1.arcgis.com/ZIL9uO234SBBPGL7/arcgis/rest/services/"
    "SB79_WFL1/FeatureServer/8/query"
    "?where=1=1"
    "&outFields=TZ,Tier,DistanceRange,HeightLimit,MaxDensity,FloorAreaRatio"
    "&returnGeometry=true&f=geojson"
)

# ============================================================
# Local cache paths
# ============================================================

CACHE_DIR = Path(__file__).parent / "cache"
PARCELS_CACHE = CACHE_DIR / "sf_parcels.geojson"
ZONING_CACHE = CACHE_DIR / "sf_zoning.geojson"
HEIGHT_CACHE = CACHE_DIR / "sf_height_districts.geojson"
HISTORIC_CACHE = CACHE_DIR / "sf_historic_union.geojson"
SLOPE_CACHE = CACHE_DIR / "sf_slopes.geojson"
OPEN_SPACE_CACHE = CACHE_DIR / "sf_open_space.geojson"

# Building footprints (local file - not from ArcGIS)
BUILDING_FOOTPRINTS_PATH = Path(__file__).parent / "Building_Footprints_20251217.geojson"

# ============================================================
# Assumptions (conservative, explicit)
# ============================================================

AVG_UNIT_SF = 800.0
EFFICIENCY = 0.85
ACRE_SF = 43560.0
FLOOR_HEIGHT_FT = 10.0  # Typical floor height in feet
FLOOR_HEIGHT_M = 3.0    # Typical floor height in meters
UTILIZATION_THRESHOLD = 0.8  # Exclude parcels with >80% utilization
SQ_FT_PER_SQ_M = 10.764  # Conversion factor

BASELINE_ZONING = {
    "RH-1": dict(du_ac=30, far=1.5),
    "RH-2": dict(du_ac=45, far=1.8),
    "RH-3": dict(du_ac=60, far=2.0),
    "RM-1": dict(du_ac=90, far=2.5),
    "RM-2": dict(du_ac=120, far=3.0),
    "RM-3": dict(du_ac=150, far=3.5),
}

# Feasibility factors - differentiated by constraint type
# These represent the probability that a parcel WILL be redeveloped over ~20 years.
# Conservative estimates based on typical planning study assumptions.
#
# Key barriers to redevelopment:
# - Owner must want to sell/develop (many long-term homeowners won't)
# - Financing and construction costs
# - Tenant protections (Ellis Act, rent control compliance)
# - Assembly and entitlement challenges

# Historic constraints - differentiated by protection level
FEASIBILITY_LANDMARK = 0.02         # Individually designated landmarks - very rare exceptions
FEASIBILITY_INDIVIDUAL_HISTORIC = 0.10  # Has HRR rating - CEQA review + preservation concerns
FEASIBILITY_HISTORIC_DISTRICT = 0.15    # In a historic district - design review adds friction
FEASIBILITY_SURVEYED = 0.18         # Surveyed properties - evaluation required

# Other constraints
FEASIBILITY_STEEP_SLOPE = 0.12      # >25% grade - engineering challenges
FEASIBILITY_MODERATE_SLOPE = 0.18   # 20-25% grade - minor impact
FEASIBILITY_SMALL_LOT = 0.15        # Lots <2500 sqft - harder to pencil financially
FEASIBILITY_TIER1 = 0.25            # Best SB79 tier - most favorable conditions
FEASIBILITY_DEFAULT = 0.20          # Base feasibility for unconstrained parcels

# ============================================================
# Helpers
# ============================================================

def units_allowed(area_sf, du_ac, far):
    by_density = du_ac * (area_sf / ACRE_SF)
    by_far = (area_sf * far * EFFICIENCY) / AVG_UNIT_SF
    return min(by_density, by_far)

def download_geojson(url, paginate=True, cache_path=None):
    """Download GeoJSON from ArcGIS REST API with pagination and caching support."""
    
    # Check cache first
    if cache_path and cache_path.exists():
        print(f"  Loading from cache: {cache_path}")
        return gpd.read_file(cache_path)
    
    if not paginate:
        r = requests.get(url)
        r.raise_for_status()
        gdf = gpd.read_file(BytesIO(r.content))
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            gdf.to_file(cache_path, driver="GeoJSON")
            print(f"  Cached to: {cache_path}")
        return gdf
    
    # Parse base URL and existing params
    if "?" in url:
        base_url, query_string = url.split("?", 1)
    else:
        base_url, query_string = url, ""
    
    # Build params dict from existing query string
    params = {}
    for part in query_string.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            params[k] = v
    
    # First, get the total count
    count_params = params.copy()
    count_params["returnCountOnly"] = "true"
    count_params["f"] = "json"
    r = requests.get(base_url, params=count_params)
    r.raise_for_status()
    total_count = r.json().get("count", 0)
    print(f"  Total records: {total_count:,}")
    
    # Paginate through all records
    all_gdfs = []
    batch_size = 2000
    offset = 0
    
    while offset < total_count:
        batch_params = params.copy()
        batch_params["resultOffset"] = str(offset)
        batch_params["resultRecordCount"] = str(batch_size)
        
        r = requests.get(base_url, params=batch_params)
        r.raise_for_status()
        
        gdf = gpd.read_file(BytesIO(r.content))
        if len(gdf) == 0:
            break
        
        all_gdfs.append(gdf)
        offset += len(gdf)
        print(f"  Downloaded {offset:,} / {total_count:,} records...")
    
    if not all_gdfs:
        raise ValueError("No records downloaded")
    
    # Concatenate and ensure it's a GeoDataFrame
    combined = pd.concat(all_gdfs, ignore_index=True)
    result = gpd.GeoDataFrame(combined, geometry="geometry", crs=all_gdfs[0].crs)
    
    # Cache the result
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        result.to_file(cache_path, driver="GeoJSON")
        print(f"  Cached to: {cache_path}")
    
    return result

def cleanup_sjoin(df):
    return df.drop(
        columns=[c for c in ["index_left", "index_right"] if c in df.columns],
        errors="ignore"
    )

# ============================================================
# Load data
# ============================================================

print("Loading parcels...")
parcels = download_geojson(SF_PARCELS_URL, cache_path=PARCELS_CACHE)

print("Loading zoning districts...")
zoning = download_geojson(SF_ZONING_URL, cache_path=ZONING_CACHE)

print("Loading height districts...")
height_districts = download_geojson(SF_HEIGHT_URL, cache_path=HEIGHT_CACHE)

# Load historic constraint layers and union them
# NOTE: Layer 0 (historic_resources) contains ALL buildings, not just historic ones!
# We need to filter based on rating fields.
print("Loading historic constraint layers...")
if HISTORIC_CACHE.exists():
    print(f"  Loading from cache: {HISTORIC_CACHE}")
    historic_union = gpd.read_file(HISTORIC_CACHE)
else:
    historic_gdfs = []
    for name, layer_id in HISTORIC_LAYERS.items():
        print(f"  Downloading {name} (layer {layer_id})...")
        try:
            gdf = download_geojson(make_planning_url(layer_id), paginate=True, cache_path=None)
            original_count = len(gdf)
            
            # Layer 0 (historic_resources) needs filtering - it contains ALL buildings
            # Only include buildings with actual historic ratings
            if name == "historic_resources":
                # Filter for buildings with historic ratings:
                # - hrrrating is not null (has a historic resource rating)
                # - OR certain ceqacode values indicate historic status
                # CEQA codes: A=Known historic, B=Needs evaluation, C=Not historic
                historic_filter = (
                    gdf["hrrrating"].notna() |  # Has a historic rating
                    (gdf["ceqacode"] == "A")     # Known historic resource
                )
                gdf = gdf[historic_filter]
                print(f"    Filtered historic_resources: {original_count:,} → {len(gdf):,} (actual historic)")
            
            # Layer 30 (historic_survey) also needs filtering
            elif name == "historic_survey":
                # Filter for properties with significant ratings
                # Ratings: A, B, C indicate historic significance; D, E, F are not historic
                if "Rating" in gdf.columns:
                    historic_filter = gdf["Rating"].isin(["A", "B", "C", "1A", "1B", "1C", "2A", "2B", "2C", "3A", "3B", "3C"])
                    gdf = gdf[historic_filter]
                    print(f"    Filtered historic_survey: {original_count:,} → {len(gdf):,} (significant ratings)")
            
            if len(gdf) > 0:
                gdf["historic_layer"] = name
                historic_gdfs.append(gdf)
                print(f"    Got {len(gdf):,} features")
            else:
                print(f"    No features after filtering")
                
        except Exception as e:
            print(f"    Warning: Failed to load {name}: {e}")
    
    if historic_gdfs:
        # Union all historic geometries
        historic_union = pd.concat(historic_gdfs, ignore_index=True)
        historic_union = gpd.GeoDataFrame(historic_union, geometry="geometry", crs=historic_gdfs[0].crs)
        # Keep individual features (don't dissolve) so we can check intersection
        historic_union["is_historic_area"] = True
        HISTORIC_CACHE.parent.mkdir(parents=True, exist_ok=True)
        historic_union.to_file(HISTORIC_CACHE, driver="GeoJSON")
        print(f"  Cached union to: {HISTORIC_CACHE}")
        print(f"  Total historic features: {len(historic_union):,}")
    else:
        historic_union = None

# Load slope layers
print("Loading slope layers...")
if SLOPE_CACHE.exists():
    print(f"  Loading from cache: {SLOPE_CACHE}")
    slopes = gpd.read_file(SLOPE_CACHE)
else:
    slope_gdfs = []
    for name, layer_id in SLOPE_LAYERS.items():
        print(f"  Downloading {name} (layer {layer_id})...")
        try:
            gdf = download_geojson(make_planning_url(layer_id), paginate=True, cache_path=None)
            gdf["slope_class"] = name
            slope_gdfs.append(gdf)
            print(f"    Got {len(gdf):,} features")
        except Exception as e:
            print(f"    Warning: Failed to load {name}: {e}")
    
    if slope_gdfs:
        slopes = pd.concat(slope_gdfs, ignore_index=True)
        slopes = gpd.GeoDataFrame(slopes, geometry="geometry", crs=slope_gdfs[0].crs)
        SLOPE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        slopes.to_file(SLOPE_CACHE, driver="GeoJSON")
        print(f"  Cached to: {SLOPE_CACHE}")
    else:
        slopes = None

# Load open space
print("Loading open space...")
open_space = download_geojson(make_planning_url(OPEN_SPACE_LAYER), cache_path=OPEN_SPACE_CACHE)

# Load building footprints (local file)
print("Loading building footprints...")
if BUILDING_FOOTPRINTS_PATH.exists():
    buildings = gpd.read_file(BUILDING_FOOTPRINTS_PATH)
    print(f"  Loaded {len(buildings):,} building footprints")
else:
    print(f"  Warning: Building footprints not found at {BUILDING_FOOTPRINTS_PATH}")
    buildings = None

print("Downloading SB79 tiers...")  # Don't cache SB79 - may change
sb79 = download_geojson(SB79_URL, cache_path=None)

# Reproject to planar CRS for area math
CRS = "EPSG:26910"  # UTM zone 10N (SF)
parcels = parcels.to_crs(CRS)
zoning = zoning.to_crs(CRS)
height_districts = height_districts.to_crs(CRS)
if historic_union is not None:
    historic_union = historic_union.to_crs(CRS)
if slopes is not None:
    slopes = slopes.to_crs(CRS)
open_space = open_space.to_crs(CRS)
if buildings is not None:
    buildings = buildings.to_crs(CRS)
sb79 = sb79.to_crs(CRS)

# ============================================================
# Prepare parcel points
# ============================================================

# Preserve original parcel geometry separately
# geometry.area is in CRS units (sq meters for UTM) - convert to sq ft
parcels["parcel_area_sf"] = parcels.geometry.area * SQ_FT_PER_SQ_M
parcels["parcel_id"] = parcels.index  # stable id for dedup

parcels_pts = parcels.copy()
parcels_pts.geometry = parcels.geometry.centroid

# ============================================================
# Calculate existing built area from building footprints
# ============================================================

if buildings is not None:
    print("Calculating existing built area from building footprints...")
    
    # Calculate footprint area in sq ft (geometry is in meters after reprojection)
    buildings["footprint_area_sqft"] = buildings.geometry.area * SQ_FT_PER_SQ_M
    
    # Get building height - use hgt_median_m if available, otherwise estimate
    if "hgt_median_m" in buildings.columns:
        buildings["height_m"] = pd.to_numeric(buildings["hgt_median_m"], errors="coerce")
    elif "hgt_mediancm" in buildings.columns:
        buildings["height_m"] = pd.to_numeric(buildings["hgt_mediancm"], errors="coerce") / 100
    else:
        # Default to 2 stories (~6m) if no height data
        buildings["height_m"] = 6.0
    
    # Fill missing heights with default (2 stories)
    buildings["height_m"] = buildings["height_m"].fillna(6.0)
    
    # Estimate number of floors
    buildings["est_floors"] = (buildings["height_m"] / FLOOR_HEIGHT_M).clip(lower=1)
    
    # Calculate gross floor area (footprint × floors)
    buildings["gross_floor_area_sqft"] = buildings["footprint_area_sqft"] * buildings["est_floors"]
    
    print(f"  Building height stats: min={buildings['height_m'].min():.1f}m, "
          f"median={buildings['height_m'].median():.1f}m, max={buildings['height_m'].max():.1f}m")
    
    # Spatial join: find which parcel each building is in
    # Use "intersects" instead of "within" because building footprints often 
    # extend slightly beyond parcel boundaries
    print("  Joining buildings to parcels...")
    buildings["building_id"] = buildings.index  # Create building ID for dedup
    buildings_with_parcel = gpd.sjoin(
        buildings,
        parcels[["geometry", "parcel_id"]],
        how="left",
        predicate="intersects",
    )
    buildings_with_parcel = cleanup_sjoin(buildings_with_parcel)
    
    # Dedup: each building should only count for one parcel
    # Keep first match (arbitrary but consistent)
    buildings_with_parcel = buildings_with_parcel.drop_duplicates(subset=["building_id"])
    
    # Aggregate: sum gross floor area per parcel
    parcel_built_area = (
        buildings_with_parcel
        .groupby("parcel_id")
        .agg(
            total_built_sqft=("gross_floor_area_sqft", "sum"),
            num_buildings=("gross_floor_area_sqft", "count"),
        )
        .reset_index()
    )
    
    print(f"  Matched {len(parcel_built_area):,} parcels with buildings")
else:
    parcel_built_area = None

# ============================================================
# Join parcels → zoning
# ============================================================

print("Joining parcels to zoning...")
parcel_zoning = gpd.sjoin(
    parcels_pts,
    zoning,
    how="left",
    predicate="within",
    lsuffix="parcel",
    rsuffix="zoning",
)
parcel_zoning = cleanup_sjoin(parcel_zoning)

# Deduplicate: one zoning per parcel
parcel_zoning = parcel_zoning.drop_duplicates("parcel_id")

# ============================================================
# Join parcels → height districts
# ============================================================

print("Joining parcels to height districts...")
# Columns are lowercase: height, gen_hght
height_cols = ["geometry", "height", "gen_hght"]
parcel_height = gpd.sjoin(
    parcels_pts,
    height_districts[height_cols],
    how="left",
    predicate="within",
)
parcel_height = cleanup_sjoin(parcel_height)
parcel_height = parcel_height.drop_duplicates("parcel_id")

# ============================================================
# Join parcels → historic constraints
# ============================================================

print("Checking parcels for historic constraints...")

# Define which layers are individual designations vs district-level
INDIVIDUAL_HISTORIC_LAYERS = {"landmarks", "historic_resources"}  # Individual buildings
DISTRICT_HISTORIC_LAYERS = {"national_register", "california_register", "article10_districts", "article11_districts"}
SURVEYED_HISTORIC_LAYERS = {"historic_survey"}  # Surveyed but not necessarily designated

if historic_union is not None and len(historic_union) > 0:
    print(f"  DEBUG - Historic union has {len(historic_union):,} geometries")
    
    # Show feature counts by layer
    if "historic_layer" in historic_union.columns:
        print("  Features by layer:")
        for layer, count in historic_union["historic_layer"].value_counts().items():
            print(f"    {layer}: {count:,}")
    
    # Check if is_historic_area column exists
    if "is_historic_area" not in historic_union.columns:
        print("  WARNING: is_historic_area column missing, adding it")
        historic_union["is_historic_area"] = True
    
    # Include historic_layer in join for analysis
    join_cols = ["geometry", "is_historic_area"]
    if "historic_layer" in historic_union.columns:
        join_cols.append("historic_layer")
    
    parcel_historic = gpd.sjoin(
        parcels,  # Use polygons for intersection
        historic_union[join_cols],
        how="left",
        predicate="intersects",
    )
    parcel_historic = cleanup_sjoin(parcel_historic)
    
    # Track which type of historic constraint each parcel has (most restrictive wins)
    # Priority: individual landmark > individual historic resource > district > surveyed
    parcel_historic_type = parcel_historic.groupby("parcel_id").agg({
        "historic_layer": lambda x: set(x.dropna())
    }).reset_index()
    parcel_historic_type.columns = ["parcel_id", "historic_layers"]
    
    def classify_historic_type(layers):
        """Classify parcel by most restrictive historic type"""
        if not layers or len(layers) == 0:
            return None
        if "landmarks" in layers:
            return "landmark"  # Most restrictive
        if "historic_resources" in layers:
            return "individual"  # Individual designated
        if layers & DISTRICT_HISTORIC_LAYERS:
            return "district"  # In a district but not individually designated
        if layers & SURVEYED_HISTORIC_LAYERS:
            return "surveyed"  # Surveyed but not designated
        return None
    
    parcel_historic_type["historic_type"] = parcel_historic_type["historic_layers"].apply(classify_historic_type)
    
    # Count by type
    print("  Parcels by historic constraint type:")
    type_counts = parcel_historic_type[parcel_historic_type["historic_type"].notna()]["historic_type"].value_counts()
    for htype, count in type_counts.items():
        print(f"    {htype}: {count:,} parcels")
    
    # Before dedup stats
    if "historic_layer" in parcel_historic.columns:
        print("  DEBUG - Parcels flagged by layer (before dedup):")
        layer_parcel_counts = parcel_historic[parcel_historic["historic_layer"].notna()].groupby("historic_layer")["parcel_id"].nunique()
        for layer, count in layer_parcel_counts.sort_values(ascending=False).items():
            print(f"    {layer}: {count:,} parcels")
    
    parcel_historic = parcel_historic.drop_duplicates("parcel_id")
    # Mark as historic if it intersected with any historic area
    parcel_historic["is_historic"] = parcel_historic["is_historic_area"].notna()
    historic_parcel_ids = set(parcel_historic[parcel_historic["is_historic"]]["parcel_id"])
    print(f"  Total historic parcels (after dedup): {len(historic_parcel_ids):,}")
else:
    parcel_historic_type = None
    historic_parcel_ids = set()
    print("  DEBUG - No historic union data")

# ============================================================
# Join parcels → slope constraints
# ============================================================

print("Checking parcels for slope constraints...")
if slopes is not None and len(slopes) > 0:
    # Check for steep slopes (>25%)
    steep_slopes = slopes[slopes["slope_class"] == "slope_25_plus"]
    if len(steep_slopes) > 0:
        parcel_steep = gpd.sjoin(
            parcels,
            steep_slopes,
            how="left",
            predicate="intersects",
        )
        parcel_steep = cleanup_sjoin(parcel_steep)
        parcel_steep = parcel_steep.drop_duplicates("parcel_id")
        steep_parcel_ids = set(parcel_steep[parcel_steep["slope_class"].notna()]["parcel_id"])
    else:
        steep_parcel_ids = set()
    
    # Check for moderate slopes (20-25%)
    moderate_slopes = slopes[slopes["slope_class"] == "slope_20_25"]
    if len(moderate_slopes) > 0:
        parcel_moderate = gpd.sjoin(
            parcels,
            moderate_slopes,
            how="left",
            predicate="intersects",
        )
        parcel_moderate = cleanup_sjoin(parcel_moderate)
        parcel_moderate = parcel_moderate.drop_duplicates("parcel_id")
        moderate_parcel_ids = set(parcel_moderate[parcel_moderate["slope_class"].notna()]["parcel_id"])
    else:
        moderate_parcel_ids = set()
else:
    steep_parcel_ids = set()
    moderate_parcel_ids = set()

# ============================================================
# Join parcels → open space (exclude entirely)
# ============================================================

print("Checking parcels for open space...")
open_space["is_open_space"] = True
parcel_openspace = gpd.sjoin(
    parcels,
    open_space[["geometry", "is_open_space"]],
    how="left",
    predicate="intersects",
)
parcel_openspace = cleanup_sjoin(parcel_openspace)
parcel_openspace = parcel_openspace.drop_duplicates("parcel_id")
openspace_parcel_ids = set(parcel_openspace[parcel_openspace["is_open_space"].notna()]["parcel_id"])

# ============================================================
# Join parcels → SB79 tiers (POLYGON INTERSECTION, not centroid)
# ============================================================

print("Joining parcels to SB79 tiers...")
print(f"  Total parcels: {len(parcels):,}")
print(f"  SB79 polygons: {len(sb79):,}")

parcel_sb79 = gpd.sjoin(
    parcels,            # polygons
    sb79,               # polygons
    how="left",
    predicate="intersects",
    lsuffix="parcel",
    rsuffix="sb79",
)
parcel_sb79 = cleanup_sjoin(parcel_sb79)

# Count before deduplication (some parcels may intersect multiple SB79 zones)
sb79_matches_before_dedup = parcel_sb79[parcel_sb79["TZ"].notna()]
print(f"  Parcels intersecting SB79 (before dedup): {len(sb79_matches_before_dedup):,}")
print(f"  Unique parcels intersecting SB79: {sb79_matches_before_dedup['parcel_id'].nunique():,}")

# If a parcel intersects multiple SB79 polygons,
# keep the MOST PERMISSIVE one (max density, then max FAR)
parcel_sb79 = (
    parcel_sb79
    .sort_values(
        by=["MaxDensity", "FloorAreaRatio"],
        ascending=False,
        na_position="last",
    )
    .drop_duplicates("parcel_id")
)

sb79_final_count = parcel_sb79[parcel_sb79["TZ"].notna()]
print(f"  Final parcels in SB79 zones: {len(sb79_final_count):,}")

# ============================================================
# Merge zoning + height + SB79 info + constraints
# ============================================================

print("Merging all data...")
parcel_all = parcel_zoning.merge(
    parcel_height[["parcel_id", "height", "gen_hght"]],
    on="parcel_id",
    how="left",
)

parcel_all = parcel_all.merge(
    parcel_sb79[["parcel_id", "TZ", "Tier", "DistanceRange", "HeightLimit", "MaxDensity", "FloorAreaRatio"]],
    on="parcel_id",
    how="left",
)

# Add constraint flags
parcel_all["is_historic"] = parcel_all["parcel_id"].isin(historic_parcel_ids)
parcel_all["is_steep_slope"] = parcel_all["parcel_id"].isin(steep_parcel_ids)
parcel_all["is_moderate_slope"] = parcel_all["parcel_id"].isin(moderate_parcel_ids)
parcel_all["is_open_space"] = parcel_all["parcel_id"].isin(openspace_parcel_ids)

# Add historic type (landmark, individual, district, surveyed)
if parcel_historic_type is not None:
    parcel_all = parcel_all.merge(
        parcel_historic_type[["parcel_id", "historic_type"]],
        on="parcel_id",
        how="left",
    )

# ============================================================
# Add existing built area and calculate utilization
# ============================================================

if parcel_built_area is not None:
    print("Adding built area and calculating utilization...")
    parcel_all = parcel_all.merge(
        parcel_built_area,
        on="parcel_id",
        how="left",
    )
    parcel_all["total_built_sqft"] = parcel_all["total_built_sqft"].fillna(0)
    parcel_all["num_buildings"] = parcel_all["num_buildings"].fillna(0)
    
    # Calculate existing FAR (built area / parcel area)
    parcel_all["existing_far"] = parcel_all["total_built_sqft"] / parcel_all["parcel_area_sf"]
    
    # Debug: Check FloorAreaRatio values
    print(f"\n  DEBUG - FloorAreaRatio column type: {parcel_all['FloorAreaRatio'].dtype}")
    print(f"  DEBUG - FloorAreaRatio non-null count: {parcel_all['FloorAreaRatio'].notna().sum():,}")
    print(f"  DEBUG - FloorAreaRatio sample values: {parcel_all['FloorAreaRatio'].dropna().head(10).tolist()}")
    
    # Ensure FloorAreaRatio is numeric
    parcel_all["FloorAreaRatio"] = pd.to_numeric(parcel_all["FloorAreaRatio"], errors="coerce")
    
    # Debug: Check existing_far values for SB79 parcels
    sb79_parcels_debug = parcel_all[parcel_all["FloorAreaRatio"].notna()]
    if len(sb79_parcels_debug) > 0:
        print(f"  DEBUG - SB79 parcels: {len(sb79_parcels_debug):,}")
        print(f"  DEBUG - SB79 FAR range: {sb79_parcels_debug['FloorAreaRatio'].min():.2f} to {sb79_parcels_debug['FloorAreaRatio'].max():.2f}")
        print(f"  DEBUG - Existing FAR for SB79 parcels: min={sb79_parcels_debug['existing_far'].min():.2f}, "
              f"median={sb79_parcels_debug['existing_far'].median():.2f}, max={sb79_parcels_debug['existing_far'].max():.2f}")
    
    # Calculate utilization against SB79 FAR (not baseline!)
    # The point is: how much of the UPZONED capacity is already used?
    # A parcel at 100% of baseline but only 50% of SB79 is a great candidate!
    def get_sb79_utilization(row):
        existing = row["existing_far"]
        if existing == 0:
            return 0.0
        
        # For parcels in SB79 zones, use the SB79 FAR
        sb79_far = row.get("FloorAreaRatio")
        if pd.notna(sb79_far) and sb79_far > 0:
            return existing / float(sb79_far)
        
        # For parcels NOT in SB79 zones, don't filter by utilization
        # (they won't benefit from upzoning anyway)
        return 0.0
    
    parcel_all["utilization"] = parcel_all.apply(get_sb79_utilization, axis=1).clip(upper=2.0)
    
    # Also calculate baseline utilization for reference
    def get_baseline_far(row):
        height_ft = row.get("gen_hght")
        if pd.notna(height_ft) and height_ft > 0:
            max_floors = height_ft / FLOOR_HEIGHT_FT
            return max_floors * 0.8
        zone = row.get("zoning")
        if zone in BASELINE_ZONING:
            return BASELINE_ZONING[zone]["far"]
        return 1.5
    
    parcel_all["baseline_far"] = parcel_all.apply(get_baseline_far, axis=1)
    parcel_all["baseline_utilization"] = (parcel_all["existing_far"] / parcel_all["baseline_far"]).clip(upper=2.0)
    
    print(f"  Parcels with buildings: {(parcel_all['num_buildings'] > 0).sum():,}")
    print(f"  Baseline utilization: min={parcel_all['baseline_utilization'].min():.2f}, "
          f"median={parcel_all['baseline_utilization'].median():.2f}, max={parcel_all['baseline_utilization'].max():.2f}")
    
    # Only look at SB79 parcels for utilization stats
    sb79_mask = parcel_all["FloorAreaRatio"].notna()
    if sb79_mask.any():
        sb79_util = parcel_all.loc[sb79_mask, "utilization"]
        print(f"  SB79 utilization (vs upzoned FAR): min={sb79_util.min():.2f}, "
              f"median={sb79_util.median():.2f}, max={sb79_util.max():.2f}")
    
    # Flag highly utilized parcels (relative to SB79 capacity)
    parcel_all["is_highly_utilized"] = parcel_all["utilization"] > UTILIZATION_THRESHOLD
    print(f"  Highly utilized vs SB79 FAR (>{UTILIZATION_THRESHOLD:.0%}): {parcel_all['is_highly_utilized'].sum():,}")
else:
    parcel_all["total_built_sqft"] = 0
    parcel_all["existing_far"] = 0
    parcel_all["utilization"] = 0
    parcel_all["baseline_utilization"] = 0
    parcel_all["is_highly_utilized"] = False

# ============================================================
# Exclude open space parcels entirely
# ============================================================

initial_count = len(parcel_all)
parcel_all = parcel_all[~parcel_all["is_open_space"]]
excluded_openspace = initial_count - len(parcel_all)
print(f"Excluded {excluded_openspace:,} open space parcels")

# ============================================================
# Exclude very large parcels (likely institutional, parks, etc.)
# ============================================================

# Typical SF residential lot is 2,500-5,000 sqft
# Parcels over 1 acre (43,560 sqft) are unusual for residential
# Parcels over 0.5 acres (21,780 sqft) should be treated skeptically
MAX_PARCEL_SQFT = 43560  # 1 acre

initial_count = len(parcel_all)
parcel_all = parcel_all[parcel_all["parcel_area_sf"] <= MAX_PARCEL_SQFT]
excluded_large = initial_count - len(parcel_all)
print(f"Excluded {excluded_large:,} parcels over 1 acre (likely institutional/parks)")

# ============================================================
# Exclude highly utilized parcels
# ============================================================

print(f"\n  DEBUG - is_highly_utilized True count: {parcel_all['is_highly_utilized'].sum():,}")
print(f"  DEBUG - utilization > {UTILIZATION_THRESHOLD} count: {(parcel_all['utilization'] > UTILIZATION_THRESHOLD).sum():,}")

initial_count = len(parcel_all)
parcel_all = parcel_all[~parcel_all["is_highly_utilized"]]
excluded_utilized = initial_count - len(parcel_all)
print(f"Excluded {excluded_utilized:,} highly utilized parcels (>{UTILIZATION_THRESHOLD:.0%})")

# ============================================================
# Constraint summary
# ============================================================

print(f"\n=== Constraint Summary ===")
print(f"Historic parcels (any type): {parcel_all['is_historic'].sum():,}")
if "historic_type" in parcel_all.columns:
    print("  Historic parcel breakdown:")
    hist_counts = parcel_all["historic_type"].value_counts(dropna=False)
    for htype, count in hist_counts.items():
        if pd.notna(htype):
            feasibility_rate = {
                "landmark": FEASIBILITY_LANDMARK,
                "individual": FEASIBILITY_INDIVIDUAL_HISTORIC,
                "district": FEASIBILITY_HISTORIC_DISTRICT,
                "surveyed": FEASIBILITY_SURVEYED,
            }.get(htype, "N/A")
            print(f"    {htype}: {count:,} parcels @ {feasibility_rate:.0%} feasibility")
print(f"Steep slope (>25%) parcels: {parcel_all['is_steep_slope'].sum():,}")
print(f"Moderate slope (20-25%) parcels: {parcel_all['is_moderate_slope'].sum():,}")
print(f"Total parcels after exclusions: {len(parcel_all):,}")

# ============================================================
# Baseline capacity (using height district for better estimate)
# ============================================================

def baseline_units(row):
    zone = row.get("zoning")
    area_sf = row["parcel_area_sf"]
    
    # Get height limit from height district (in feet)
    height_ft = row.get("gen_hght")
    
    # Handle special height codes:
    # 8888 = "unlimited" or "no limit specified" - cap at realistic max
    # Values > 1000 are likely special codes, not actual heights
    if pd.notna(height_ft) and height_ft > 0:
        if height_ft >= 1000:
            # Special code - use reasonable default (400 ft = ~40 floors)
            height_ft = 400
        # Estimate max floors from height district
        max_floors = height_ft / FLOOR_HEIGHT_FT
        # Calculate effective FAR from height (with typical lot coverage ~0.8)
        height_based_far = max_floors * 0.8
    else:
        height_based_far = 2.0  # Default if no height data
    
    if zone in BASELINE_ZONING:
        z = BASELINE_ZONING[zone]
        # Use the MORE RESTRICTIVE of zoning FAR or height-based FAR
        effective_far = z["far"]
        if height_based_far < effective_far:
            effective_far = height_based_far
        return units_allowed(area_sf, z["du_ac"], effective_far)
    
    # For zones not in our baseline dict (commercial, mixed-use, etc.):
    # Estimate baseline from height district only, with typical density assumptions
    # These zones often already allow high density, sometimes exceeding SB79
    if height_based_far:
        # Use height-based FAR with a moderate density assumption (100 du/acre)
        # This is conservative - many commercial zones allow more
        return units_allowed(area_sf, 100, height_based_far)
    
    return 0.0

parcel_all["baseline_units"] = parcel_all.apply(baseline_units, axis=1)

# ============================================================
# SB79 capacity (use layer attributes directly)
# ============================================================

def sb79_units(row):
    if pd.isna(row.get("MaxDensity")) or pd.isna(row.get("FloorAreaRatio")):
        return 0.0
    return units_allowed(
        row["parcel_area_sf"],
        float(row["MaxDensity"]),
        float(row["FloorAreaRatio"]),
    )

parcel_all["sb79_units"] = parcel_all.apply(sb79_units, axis=1)

# ============================================================
# Added capacity
# ============================================================

parcel_all["added_units_theoretical"] = (
    parcel_all["sb79_units"] - parcel_all["baseline_units"]
).clip(lower=0)

# ============================================================
# Feasibility factors with constraints
# ============================================================

def feasibility(row):
    # Historic properties - use differentiated rates based on type
    historic_type = row.get("historic_type")
    if historic_type == "landmark":
        return FEASIBILITY_LANDMARK
    elif historic_type == "individual":
        return FEASIBILITY_INDIVIDUAL_HISTORIC
    elif historic_type == "district":
        return FEASIBILITY_HISTORIC_DISTRICT
    elif historic_type == "surveyed":
        return FEASIBILITY_SURVEYED
    
    # For slopes: if parcel already has buildings, slope is clearly buildable - no discount
    has_buildings = row.get("num_buildings", 0) > 0
    
    # Steep slopes get discount (unless already built)
    if row.get("is_steep_slope") and not has_buildings:
        return FEASIBILITY_STEEP_SLOPE
    
    # Moderate slopes get slight discount (unless already built)
    if row.get("is_moderate_slope") and not has_buildings:
        return FEASIBILITY_MODERATE_SLOPE
    
    # Small lots are harder to develop
    if row["parcel_area_sf"] < 2500:
        return FEASIBILITY_SMALL_LOT
    
    # Tier 1 zones are most favorable
    if row.get("TZ") in ("T1Z1", "T1Z2"):
        return FEASIBILITY_TIER1

    return FEASIBILITY_DEFAULT

parcel_all["feasibility_factor"] = parcel_all.apply(feasibility, axis=1)
parcel_all["added_units_realistic"] = (
    parcel_all["added_units_theoretical"] * parcel_all["feasibility_factor"]
)

# ============================================================
# Results
# ============================================================

print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

print(f"\nTotal parcels analyzed: {len(parcel_all):,}")

print("\n=== Height District distribution ===")
print(parcel_all["gen_hght"].value_counts(dropna=False).head(15))

print("\n=== SB79 Tier distribution (parcels) ===")
print(parcel_all["TZ"].value_counts(dropna=False))

# Only count parcels that are in SB79 zones
sb79_parcels = parcel_all[parcel_all["TZ"].notna()]
print(f"\nParcels in SB79 zones: {len(sb79_parcels):,}")

# Debug: understand the theoretical capacity
print("\n=== DEBUG: Zoning distribution ===")
print(parcel_all["zoning"].value_counts(dropna=False).head(20))

# Check how many parcels are in our BASELINE_ZONING dict
baseline_zones = list(BASELINE_ZONING.keys())
in_baseline_zoning = parcel_all["zoning"].isin(baseline_zones).sum()
print(f"\nParcels in RH/RM zones (baseline defined): {in_baseline_zoning:,}")
print(f"Parcels NOT in RH/RM zones: {len(parcel_all) - in_baseline_zoning:,}")

print("\n=== DEBUG: Theoretical capacity breakdown ===")
parcels_with_capacity = parcel_all[parcel_all["added_units_theoretical"] > 0]
print(f"Parcels with added_units_theoretical > 0: {len(parcels_with_capacity):,}")
print(f"Parcels with sb79_units > 0: {(parcel_all['sb79_units'] > 0).sum():,}")
print(f"Parcels with baseline_units > 0: {(parcel_all['baseline_units'] > 0).sum():,}")
print(f"Parcels where sb79 > baseline: {(parcel_all['sb79_units'] > parcel_all['baseline_units']).sum():,}")

# Show distribution of added capacity
if len(parcels_with_capacity) > 0:
    print(f"\nAdded capacity per parcel (where > 0):")
    print(f"  Min: {parcels_with_capacity['added_units_theoretical'].min():.2f}")
    print(f"  Median: {parcels_with_capacity['added_units_theoretical'].median():.2f}")
    print(f"  Mean: {parcels_with_capacity['added_units_theoretical'].mean():.2f}")
    print(f"  Max: {parcels_with_capacity['added_units_theoretical'].max():.2f}")
    print(f"  Total: {parcels_with_capacity['added_units_theoretical'].sum():,.0f}")

print("\n=== Utilization distribution (vs SB79 upzoned FAR) ===")
if "utilization" in parcel_all.columns and parcel_all["utilization"].sum() > 0:
    util_bins = [0, 0.25, 0.5, 0.75, 1.0, float("inf")]
    util_labels = ["0-25%", "25-50%", "50-75%", "75-100%", ">100%"]
    parcel_all["util_bin"] = pd.cut(parcel_all["utilization"], bins=util_bins, labels=util_labels)
    print(parcel_all["util_bin"].value_counts().sort_index())
    
    # Also show baseline utilization for comparison
    if "baseline_utilization" in parcel_all.columns:
        print("\n=== Baseline utilization (vs current zoning) ===")
        parcel_all["baseline_util_bin"] = pd.cut(parcel_all["baseline_utilization"], bins=util_bins, labels=util_labels)
        print(parcel_all["baseline_util_bin"].value_counts().sort_index())
else:
    print("No utilization data available")

print("\n=== Feasibility factor distribution ===")
print(parcel_all["feasibility_factor"].value_counts().sort_index())

print("\n=== Capacity by constraint type ===")
# Historic - show breakdown by type
print("Historic parcels:")
if "historic_type" in parcel_all.columns:
    for htype in ["landmark", "individual", "district", "surveyed"]:
        mask = parcel_all["historic_type"] == htype
        theoretical = parcel_all[mask]["added_units_theoretical"].sum()
        realistic = parcel_all[mask]["added_units_realistic"].sum()
        feasibility_rate = {
            "landmark": FEASIBILITY_LANDMARK,
            "individual": FEASIBILITY_INDIVIDUAL_HISTORIC,
            "district": FEASIBILITY_HISTORIC_DISTRICT,
            "surveyed": FEASIBILITY_SURVEYED,
        }.get(htype)
        print(f"  {htype:12}: {theoretical:>8,.0f} theoretical → {realistic:>8,.0f} realistic ({feasibility_rate:.0%} feasibility)")

# Total historic
total_historic_theoretical = parcel_all[parcel_all["is_historic"]]["added_units_theoretical"].sum()
total_historic_realistic = parcel_all[parcel_all["is_historic"]]["added_units_realistic"].sum()
print(f"  {'TOTAL':12}: {total_historic_theoretical:>8,.0f} theoretical → {total_historic_realistic:>8,.0f} realistic")

# Steep slope
steep_capacity = parcel_all[parcel_all["is_steep_slope"]]["added_units_theoretical"].sum()
steep_realistic = parcel_all[parcel_all["is_steep_slope"]]["added_units_realistic"].sum()
print(f"\nSteep slope (>25%): {steep_capacity:,.0f} theoretical → {steep_realistic:,.0f} realistic ({FEASIBILITY_STEEP_SLOPE:.0%} feasibility)")

# Moderate slope
moderate_capacity = parcel_all[parcel_all["is_moderate_slope"]]["added_units_theoretical"].sum()
moderate_realistic = parcel_all[parcel_all["is_moderate_slope"]]["added_units_realistic"].sum()
print(f"Moderate slope (20-25%): {moderate_capacity:,.0f} theoretical → {moderate_realistic:,.0f} realistic ({FEASIBILITY_MODERATE_SLOPE:.0%} feasibility)")

print("\n=== Capacity results ===")
print(f"Theoretical SB79 added capacity: {parcel_all['added_units_theoretical'].sum():,.0f} units")
print(f"Realistic SB79 added capacity:   {parcel_all['added_units_realistic'].sum():,.0f} units")

# ============================================================
# Export for inspection
# ============================================================

# Reproject to WGS84 (EPSG:4326) for web mapping compatibility
# (kepler.gl, geojson.io, etc. expect lat/lon coordinates)
parcel_all_wgs84 = parcel_all.to_crs("EPSG:4326")

parcel_all_wgs84.to_file(
    "sb79_sf_parcel_results.geojson",
    driver="GeoJSON"
)

print("\nWrote sb79_sf_parcel_results.geojson (WGS84 coordinates)")

