# What Could Have Been: SB79 vs SF's Family Zoning Plan 🏠

**An analysis showing how much housing San Francisco is giving up by adopting the Family Zoning Plan instead of accepting SB79.**

## The Bottom Line

| Plan | Realistic Capacity (20 years) |
|------|------------------------------|
| **SB79** | ~57,000 units |
| **Family Zoning Plan** | ~9,400 units |
| **What SF is giving up** | **~47,000 units** |

San Francisco's Family Zoning Plan delivers approximately **6x less housing** than what SB79 would provide.

## Why This Matters

California's SB79 establishes minimum zoning standards for housing near transit. Cities can exempt themselves by adopting local upzoning plans before **2032**.

San Francisco's response is the **Family Zoning Plan** — a proposal that:
- Keeps most neighborhoods at **40-foot height limits** (vs SB79's 85-105 ft)
- Maintains **density restrictions** on 112,000+ parcels
- Covers **65,000 fewer parcels** than SB79

This analysis uses the same methodology for both plans to show the real difference.

## Validation

Our FZP estimate of **~9,400 units** aligns closely with **Ted Egan** (SF City Economist), who predicted **10,000-15,000 units** from the plan over 20 years. The city's official "target" of 36,000 units appears to be theoretical, not realistic.

## ⚠️ Disclaimer

**This is an AI-assisted experiment, not professional analysis.** The methodology, feasibility factors, and calculations are exploratory. Don't use this for policy, investment, or legal purposes.

That said — our numbers match official economist estimates, so we're at least in the right ballpark.

## Key Findings

### Coverage Gap

| Metric | SB79 | FZP |
|--------|------|-----|
| Parcels covered | 143,261 | 78,115 |
| **Difference** | +65,146 | — |

### Head-to-Head (Parcels in Both Zones)

On parcels covered by **both** plans:
- **83% of parcels**: SB79 allows more housing
- **17% of parcels**: FZP allows more housing

### Where SB79 Wins Biggest

Single-family zones (RH-1, RH-1(D)) where FZP maintains 40-foot heights while SB79 allows 85-105 feet.

## Visualization

### Realistic Capacity by Parcel

![Realistic capacity increase heatmap](images/increased_capacity_realistic.png)

*SB79 capacity concentrates along transit corridors. Most individual parcels show modest increases due to feasibility discounts — the value is in the aggregate.*

### SB79 Transit Coverage

![Transit stops and SB79 zones](images/transit_stops.png)

*SB79 zones extend 0.5 miles from major transit stops. The Family Zoning Plan covers a much smaller area.*

**Explore the data:** Load `sb79_sf_parcel_results.geojson` into [kepler.gl](https://kepler.gl/demo) and color by `sb79_vs_fzp_delta` to see which parcels gain more under each plan.

## Data Sources

### Included (via Git LFS)

| File | Description |
|------|-------------|
| `sb79_sf_parcel_results.geojson` | Parcel-level results with SB79 and FZP capacity |
| `Building_Footprints_20251217.geojson` | [SF Building Footprints](https://data.sfgov.org/Geographic-Locations-and-Boundaries/Building-Footprints/ynuv-fyni/about_data) |
| `sb79_polygons.json` | [USC SSI SB79 Map](https://uscssi.maps.arcgis.com/apps/mapviewer/index.html?webmap=7689658f319b488ba03c40ccb903681e) |

### Downloaded at Runtime

From [SF Planning GIS](https://sfplanninggis.org/arcgiswa/rest/services/PlanningData/MapServer):
- Parcels, Zoning, Height Districts
- Historic constraint layers
- Slope data, Open space

From SF Planning's Rezoning Experience:
- FZP density layer (November 2025 ordinance)
- FZP height proposals

## Quick Start

```bash
pip install -r requirements.txt
python what_could_have_been.py
```

First run downloads ~250MB of GIS data (cached for subsequent runs).

## Output

The GeoJSON output includes per-parcel:
- `sb79_units` / `fzp_units` — Allowed units under each plan
- `added_units_theoretical` / `fzp_added_units_theoretical` — Added capacity vs baseline
- `added_units_realistic` / `fzp_added_units_realistic` — With feasibility discounts
- `sb79_vs_fzp_delta` — Direct comparison (positive = SB79 allows more)

## Files

| File | Description |
|------|-------------|
| `what_could_have_been.py` | Main analysis script |
| `SB79_Analysis_Report.md` | Full methodology and comparison |
| `sb79_sf_parcel_results.geojson` | Results — load in kepler.gl to explore |

## Contributing

Found an error? Know more about SF zoning than me? PRs welcome!

## License

MIT — do whatever you want with this, just don't expect it to be right.
