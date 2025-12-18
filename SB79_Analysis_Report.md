# SB79 Housing Capacity Analysis for San Francisco

**Generated:** December 18, 2025

---

## Executive Summary

This analysis estimates the potential housing capacity that could be unlocked in San Francisco under SB79, California's transit-oriented development bill. Using parcel-level geospatial data from SF Planning, we calculate both theoretical maximum capacity and a more realistic estimate accounting for development constraints.

| Metric | Value |
|--------|-------|
| **Theoretical Added Capacity** | **344,235 units** |
| **Realistic Added Capacity** | **56,547 units** |
| Weighted Feasibility Rate | 16.4% |
| SF Existing Housing Stock | ~380,000 units |
| Realistic as % of Existing | 15% |
| Annual (over 20 years) | ~2,827 units/year |

---

## Methodology Overview

### Data Sources

All geospatial data sourced from [SF Planning's ArcGIS REST services](https://sfplanninggis.org/arcgiswa/rest/services/PlanningData/MapServer):

| Layer | MapServer ID | Purpose |
|-------|--------------|---------|
| SF Parcels | 3 | Base geography (226,775 parcels) |
| Zoning Districts | 1 | Baseline density/FAR |
| Height Districts | 5 | Height limits to cap FAR |
| SB79 Tiers | 53 | Upzoned MaxDensity + FAR |
| Open Space | 20 | Exclusion layer |
| Historic Resources | 0 | Constraint layer |
| Landmarks | 11 | Constraint layer |
| Historic Districts | 6, 7, 16, 17 | Constraint layer |
| Historic Survey | 30 | Constraint layer |
| Slopes | 18, 19 | Constraint layer |
| Building Footprints | Local file | Utilization calculation |

### Processing Pipeline

1. **Load & Reproject**: All layers reprojected to EPSG:26910 (UTM Zone 10N)
2. **Spatial Joins**: Parcels joined to zoning, height, SB79, and constraint layers
3. **Calculate Baseline**: Units allowed under current zoning + height limits
4. **Calculate SB79**: Units allowed under SB79 upzoning
5. **Apply Exclusions**: Remove open space, large parcels (>1 acre)
6. **Apply Feasibility**: Discount capacity by constraint type
7. **Aggregate Results**: Sum theoretical and realistic capacity

---

## Parcel Processing Summary

| Stage | Parcels |
|-------|---------|
| Raw SF parcels loaded | 226,775 |
| After open space exclusion | 218,748 |
| After large parcel exclusion (>1 acre) | 179,213 |
| Parcels in SB79 zones | 143,261 |
| Parcels with added capacity (SB79 > baseline) | 90,881 |

---

## Exclusion Layers

Parcels in these categories are **entirely excluded** from capacity calculations:

| Layer | Parcels Excluded | Rationale |
|-------|------------------|-----------|
| Open Space (layer 20) | 8,027 | Parks/public space - not developable |
| Large parcels (>1 acre) | 16,375 | Likely institutional, parks, or data anomalies |

---

## Historic Constraint Layers

Historic constraints apply **feasibility discounts** rather than full exclusion, recognizing that development does occur on historic properties with appropriate review.

### Layer Details

| Layer | MapServer ID | Features | Processing |
|-------|--------------|----------|------------|
| **Historic Resources** | 0 | 163,160 raw → 24,767 filtered | Filtered to records with HRR rating or CEQA Category A |
| **Landmarks** | 11 | 354 | Individually designated buildings |
| **National Register Districts** | 6 | 60 | District boundaries |
| **California Register Districts** | 7 | 185 | District boundaries |
| **Article 10 Historic Districts** | 17 | 14 | Local historic districts |
| **Article 11 Conservation Districts** | 16 | 7 | Conservation districts |
| **Historic Survey** | 30 | 47,804 raw → 3,692 filtered | Filtered to significant ratings (A, B, C) |

### Classification Logic

Parcels are classified by the **most restrictive** historic constraint:

| Classification | Criteria | Feasibility | Rationale |
|---------------|----------|-------------|-----------|
| **Landmark** | Intersects layer 11 | 2% | Individually designated - extremely rare exceptions |
| **Individual** | Intersects layer 0 (Historic Resources) | 10% | Has HRR rating - CEQA review required |
| **District** | Intersects layers 6, 7, 16, or 17 | 15% | In a district but not individually designated |
| **Surveyed** | Intersects layer 30 | 18% | Surveyed with A/B/C rating |

### Historic Impact Summary

| Type | Parcels | Theoretical | Realistic | Effective Rate |
|------|---------|-------------|-----------|----------------|
| Landmark | 3,383.0 | 11,036 | 221 | 2% |
| Individual | 48,850.0 | 64,425 | 6,443 | 10% |
| District | 2,664.0 | 9,858 | 1,479 | 15% |
| Surveyed | 2,633.0 | 3,806 | 685 | 18% |
| **Total Historic** | — | 89,126 | 8,827 | 10% |

---

## Slope Constraint Layers

| Layer | MapServer ID | Parcels | Feasibility | Rationale |
|-------|--------------|---------|-------------|-----------|
| **Steep Slope (>25%)** | 18 | 67,352 | 12% | Engineering challenges, grading costs |
| **Moderate Slope (20-25%)** | 19 | 87,008 | 18% | Minor construction impact |

**Important**: Slope discounts are **only applied to undeveloped parcels**. If a parcel already has buildings, the slope is demonstrably buildable.

### Slope Impact Summary

| Slope Type | Theoretical Capacity | Realistic Capacity |
|------------|---------------------|-------------------|
| Steep (>25%) | 119,352 | 14,322 |
| Moderate (20-25%) | 156,835 | 28,230 |

---

## Other Feasibility Factors

| Constraint | Feasibility | Rationale |
|------------|-------------|-----------|
| **Small lots (<2,500 sqft)** | 15% | Harder to pencil financially |
| **Tier 1 SB79 zones** | 25% | Most favorable upzoning conditions |
| **Default (unconstrained)** | 20% | Base rate for typical development barriers |

### Why Feasibility Matters

Even without physical constraints, most parcels won't be redeveloped because:

- **Owner preferences**: Long-term homeowners may not want to sell/develop
- **Financing barriers**: Construction costs and lending requirements
- **Tenant protections**: Ellis Act compliance, rent control implications
- **Entitlement uncertainty**: Approval timeline and conditions
- **Assembly challenges**: Many optimal sites require lot consolidation

---

## Feasibility Distribution

| Rate | Constraint Type | Parcels | % Total | Theoretical | Realistic |
|------|-----------------|---------|---------|-------------|-----------|
| 2% | Landmarks | 3,383.0 | 1.9% | 11,036 | 221 |
| 10% | Individual Historic | 48,850.0 | 27.3% | 64,425 | 6,443 |
| 12% | Steep Slope | 14,850.0 | 8.3% | 23,253 | 2,790 |
| 15% | District/Small Lot | 41,722.0 | 23.3% | 78,440 | 11,766 |
| 18% | Surveyed/Moderate Slope | 5,763.0 | 3.2% | 11,846 | 2,132 |
| 20% | Default | 55,538.0 | 31.0% | 112,276 | 22,455 |
| 25% | Tier 1 SB79 | 9,107.0 | 5.1% | 42,958 | 10,740 |
| **Total** | — | **179,213** | 100% | **344,235** | **56,547** |

---

## Capacity by SB79 Tier

| Tier | Parcels | Theoretical | Realistic | Avg Units/Parcel |
|------|---------|-------------|-----------|------------------|
| T1Z1 | 10,337.0 | 70,748 | 10,720 | 6.84 |
| T1Z2 | 29,777.0 | 44,197 | 7,935 | 1.48 |
| T2Z1 | 61,211.0 | 150,032 | 24,790 | 2.45 |
| T2Z2 | 41,936.0 | 79,258 | 13,101 | 1.89 |
| **Total** | **143,261** | **344,235** | **56,547** | 2.40 |

### SB79 Tier Parameters

| Tier | Distance from Transit | MaxDensity | FAR |
|------|----------------------|------------|-----|
| T1Z1 | Within 0.25 mi of major transit | 100-120 du/acre | 3.0-3.5 |
| T1Z2 | 0.25-0.5 mi of major transit | 100-120 du/acre | 3.0-3.5 |
| T2Z1 | Within 0.25 mi of local transit | 80-100 du/acre | 2.5-3.0 |
| T2Z2 | 0.25-0.5 mi of local transit | 80-100 du/acre | 2.5-3.0 |

---

## Capacity by Zoning Type (Top 10)

| Zoning | Parcels | Theoretical | Realistic | Notes |
|--------|---------|-------------|-----------|-------|
| RH-1 | 59,091.0 | 156,565 | 27,814 | Single-family residential |
| RH-2 | 34,909.0 | 93,009 | 15,055 | Two-family residential |
| RH-3 | 12,143.0 | 36,122 | 4,952 | Three-family residential |
| C-3-G | 4,961.0 | 14,680 | 2,141 | Downtown general commercial |
| MB-RA | 599.0 | 6,525 | 1,630 |  |
| NCT-MISSION | 837.0 | 4,694 | 461 |  |
| CMUO | 1,375.0 | 4,653 | 730 |  |
| MUO | 513.0 | 4,311 | 1,066 |  |
| UMU | 2,708.0 | 3,535 | 426 |  |
| RM-1 | 8,678.0 | 3,360 | 522 | Low-density multi-family |

---

## Calculation Methodology

### Baseline Units Calculation

For residential zones (RH-1, RH-2, RH-3, RM-1, RM-2, RM-3):

```
baseline_units = min(
    parcel_area × zoning_density,
    parcel_area × effective_FAR × efficiency / avg_unit_size
)
```

Where:
- `effective_FAR` = min(zoning_FAR, height_based_FAR)
- `height_based_FAR` = (height_ft / 10) × 0.8 (lot coverage)

### Baseline Zoning Parameters

| Zone | Density (du/acre) | FAR |
|------|-------------------|-----|
| RH-1 | 30 | 1.5 |
| RH-2 | 45 | 1.8 |
| RH-3 | 60 | 2.0 |
| RM-1 | 90 | 2.5 |
| RM-2 | 120 | 3.0 |
| RM-3 | 150 | 3.5 |

### SB79 Units Calculation

```
sb79_units = min(
    parcel_area × MaxDensity,
    parcel_area × FloorAreaRatio × efficiency / avg_unit_size
)
```

### Added Capacity

```
added_theoretical = max(0, sb79_units - baseline_units)
added_realistic = added_theoretical × feasibility_factor
```



### Key Assumptions

| Parameter | Value | Notes |
|-----------|-------|-------|
| Average unit size | 800 sqft | Net livable area |
| Building efficiency | 85% | Gross-to-net ratio |
| Floor height | 10 ft | For floor count estimation |
| Lot coverage | 80% | Typical SF residential |
| Utilization threshold | 80% | Parcels above this already near capacity |

---

## Limitations & Caveats

1. **Baseline estimates are approximate**: Actual zoning allows vary by parcel-specific conditions
2. **SB79 parameters may change**: Bill implementation details still evolving
3. **Feasibility is inherently uncertain**: Actual development depends on market conditions
4. **Historic data may be incomplete**: Not all constraints captured in GIS layers
5. **Building footprint matching imperfect**: Some buildings may not match to parcels correctly
6. **Large parcels excluded**: May undercount capacity on legitimately developable large sites

---

## Data Files

| File | Description |
|------|-------------|
| `sb79_sf_parcel_results.geojson` | Full parcel-level results with all attributes |
| `cache/sf_parcels.geojson` | Cached parcel boundaries |
| `cache/sf_zoning.geojson` | Cached zoning districts |
| `cache/sf_height_districts.geojson` | Cached height districts |
| `cache/sf_historic_union.geojson` | Cached historic constraint union |
| `cache/sf_slopes.geojson` | Cached slope data |
| `cache/sf_open_space.geojson` | Cached open space |

---

*Analysis performed using Python with GeoPandas, Pandas, and Shapely.*
