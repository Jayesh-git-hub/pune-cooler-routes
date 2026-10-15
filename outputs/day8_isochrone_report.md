# Day 8 Isochrone Report

**Source Point**: Deccan Gymkhana (18.5172N, 73.8415E)
**Walking Speed**: 4.8 km/h  (~80 m/min)
**Shade Threshold for Well-Shaded**: >= 30% composite shade

---

## Standard Walk Isochrones

|   time_band_min |   ring_nodes |   ring_edges |   mean_composite_shade |   pct_well_shaded_edges |
|----------------:|-------------:|-------------:|-----------------------:|------------------------:|
|               5 |          186 |          600 |                 0.398  |                    67.7 |
|              10 |          311 |          948 |                 0.3728 |                    57.5 |
|              15 |          344 |         1030 |                 0.3633 |                    54.7 |

## Shade-Priority Walk Isochrones

|   time_band_min |   ring_nodes |   ring_edges |   mean_composite_shade |   pct_well_shaded_edges |
|----------------:|-------------:|-------------:|-----------------------:|------------------------:|
|               5 |           77 |          274 |                 0.391  |                    69.3 |
|              10 |          173 |          582 |                 0.4091 |                    69.4 |
|              15 |          211 |          668 |                 0.3741 |                    56.6 |

---

## Key Insight

The Shade-Priority isochrone shows that by biasing toward cooler shaded edges,
a walker can reach a higher proportion of well-shaded streets within the same
time window, at the cost of a slightly smaller total reachable area.

**Shade-Priority 10-min ring**: 69.4% of edges well-shaded vs 57.5% in Standard walk — +11.9% improvement!