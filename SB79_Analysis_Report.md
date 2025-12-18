# What Could Have Been: SB79 vs San Francisco's Family Zoning Plan

**Generated:** December 18, 2025

---

## The Story

California's SB79 establishes statewide minimum zoning standards for housing near transit stops. Cities can exempt themselves from SB79 by adopting qualifying local upzoning plans before 2032.

San Francisco's response? The **Family Zoning Plan (FZP)** — a proposal that appears designed to meet the bare minimum requirements for an exemption while preserving most existing restrictions.

**This analysis compares what San Francisco could build under SB79 versus what the Family Zoning Plan would actually deliver.**

---

## Executive Summary

| Plan | Theoretical Capacity | Realistic Capacity |
|------|---------------------|-------------------|
| **SB79** | 344,235 units | **56,547 units** |
| **Family Zoning Plan** | 59,065 units | **9,418 units** |
| **Difference** | +285,170 units | **+47,129 units** |

**SB79 provides approximately 6x more realistic housing capacity than the Family Zoning Plan.**

### Validation Against Official Estimates

| Source | Estimate | Notes |
|--------|----------|-------|
| City's FZP Target | 36,000 units | Official goal (theoretical) |
| Ted Egan, SF City Economist | 10,000-15,000 units | Realistic 20-year prediction |
| **Our FZP Realistic Estimate** | **9,418 units** | ✅ Aligns with Egan |
| **Our SB79 Realistic Estimate** | **56,547 units** | ~5-6x FZP |

Our methodology produces results consistent with the city's own economist's realistic projections, suggesting our feasibility factors are well-calibrated.

---

## Zone Coverage Comparison

| Metric | City's Numbers | Our Analysis |
|--------|---------------|--------------|
| Parcels in SB79 zones | 120,000 | 143,261 |
| Parcels in FZP zones | 75,000 | 78,115 |
| Parcels where SB79 > FZP | 57,000 | 51,211 |

**SB79 covers 65,000+ more parcels than FZP** — entire neighborhoods are left out of the Family Zoning Plan.

---

## Why FZP Delivers Less

### 1. Conservative Heights

| Plan | Height Distribution |
|------|-------------------|
| FZP | Median: 40 ft, Max: 400 ft |
| SB79 | 85-105 ft across tiers |

The FZP keeps most of San Francisco at **40-foot height limits** — the same as existing zoning for most residential areas.

### 2. Density-Limited Zones

| FZP Density Type | Parcels |
|------------------|---------|
| **Density-limited** | 112,146 |
| Form-based Proposed | 9,771 |
| Form-based Existing | 4,589 |

The vast majority of FZP parcels remain **"Density-limited"** — maintaining traditional density controls that cap housing production.

### 3. Narrower Geography

The FZP only covers ~78,000 parcels compared to SB79's ~143,000. Large swaths of transit-accessible San Francisco get no upzoning at all under FZP.

---

## Head-to-Head: Parcels in Both Zones

For the 61,435 parcels covered by **both** plans:

| Comparison | Parcels | Percentage |
|------------|---------|------------|
| SB79 allows more | 51,211 | **83%** |
| FZP allows more | 10,185 | 17% |
| Essentially equal | 39 | <1% |

**On 83% of overlapping parcels, SB79 would allow more housing than FZP.**

### Where SB79 Wins Biggest

| Zone | SB79 Units | FZP Units | Difference |
|------|-----------|-----------|------------|
| RH-1 (T2Z1) | 95.5 | 28.6 (40ft) | +66.9 units |
| RH-1(D) (T2Z1) | 80.4 | 24.1 (40ft) | +56.3 units |
| RH-1 (T1Z2) | 77.9 | 23.4 (40ft) | +54.5 units |

The biggest differences are in single-family zones where FZP maintains low heights.

### Where FZP Wins

| Zone | SB79 Units | FZP Units | Difference |
|------|-----------|-----------|------------|
| RH-1(D) (T2Z2) | 65.2 | 122.2 (50ft) | -57.0 units |
| NC-S (T2Z2) | 59.8 | 112.0 (50ft) | -52.3 units |

FZP occasionally exceeds SB79 in areas where FZP proposes heights above 40ft, typically in commercial/mixed-use zones.

---

## Capacity by Constraint Type

### Historic Constraints

| Type | Parcels | Theoretical | Realistic | Feasibility |
|------|---------|-------------|-----------|-------------|
| Landmark | 3,383 | 11,036 | 221 | 2% |
| Individual Historic | 48,850 | 64,425 | 6,443 | 10% |
| Historic District | 2,664 | 9,858 | 1,479 | 15% |
| Surveyed | 2,633 | 3,806 | 685 | 18% |
| **Total Historic** | 57,530 | 89,126 | 8,827 | ~10% |

### Slope Constraints

| Type | Parcels | Theoretical | Realistic | Feasibility |
|------|---------|-------------|-----------|-------------|
| Steep (>25%) | 67,352 | 119,352 | 14,322 | 12% |
| Moderate (20-25%) | 87,008 | 156,835 | 28,230 | 18% |

*Note: Slope discounts only apply to undeveloped parcels. If a parcel already has buildings, the slope is demonstrably buildable.*

---

## Methodology

### Data Sources

All geospatial data from [SF Planning's ArcGIS REST services](https://sfplanninggis.org/arcgiswa/rest/services/PlanningData/MapServer):

| Data | Source |
|------|--------|
| Parcels | SF Planning MapServer/23 |
| Zoning | SF Planning MapServer/3 |
| Height Districts | SF Planning MapServer/5 |
| Historic Layers | MapServer 0, 6, 7, 11, 16, 17, 30 |
| Slopes | MapServer 18, 19 |
| Open Space | MapServer 20 |
| SB79 Tiers | USC Spatial Sciences Institute |
| FZP Data | [SF Rezoning Experience](https://sfgov.maps.arcgis.com) (November 2025 ordinance) |

### Capacity Calculation

For both plans, we calculate:

```
units = min(
    parcel_area × density,
    parcel_area × FAR × efficiency / avg_unit_size
)
```

Where:
- `efficiency` = 85% (gross-to-net)
- `avg_unit_size` = 800 sqft

### Feasibility Factors

| Constraint | Rate | Rationale |
|------------|------|-----------|
| Landmarks | 2% | Extremely rare redevelopment |
| Individual Historic | 10% | CEQA review, preservation concerns |
| Historic District | 15% | Design review friction |
| Surveyed Historic | 18% | Evaluation required |
| Steep Slope (>25%) | 12% | Engineering challenges |
| Moderate Slope | 18% | Minor construction impact |
| Small Lots (<2,500 sqft) | 15% | Hard to pencil financially |
| Tier 1 SB79 | 25% | Most favorable conditions |
| Default | 20% | Typical development barriers |

### Exclusions

Parcels entirely excluded:
- Open space (parks, public land)
- Parcels >1 acre (likely institutional)
- Highly utilized parcels (>80% of upzoned FAR already built)

---

## Key Takeaways

1. **The gap is enormous**: SB79 would deliver ~47,000 more realistic housing units than FZP over 20 years.

2. **Our numbers match official estimates**: The SF City Economist predicted 10-15k units from FZP; our methodology produces 9.4k — validating our approach.

3. **FZP maintains the status quo**: With median heights of 40ft and most parcels "density-limited," FZP barely moves the needle.

4. **SB79 covers more ground**: 65,000+ more parcels fall within SB79 zones than FZP.

5. **The exemption deadline matters**: If SF adopts FZP before 2032, it gets to keep these restrictions. After 2032, SB79 applies statewide regardless.

---

## What This Means

By adopting the Family Zoning Plan instead of allowing SB79 to take effect, San Francisco is choosing to:

- Build **~47,000 fewer housing units** over the next 20 years
- Keep heights at 40ft across most residential neighborhoods
- Maintain density limits that prevent transit-oriented development
- Leave 65,000+ transit-accessible parcels with no upzoning

The question for San Franciscans: **Is that trade-off worth it?**

---

*Analysis performed using Python with GeoPandas. Full methodology and code available in this repository.*
