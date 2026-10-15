# Day 9 Smart Waypoint Planner Report

**Origin**: MIT-WPU Campus, Kothrud (18.5178°N, 73.8151°E)
**Destination**: Fergusson College, FC Road (18.5236°N, 73.8408°E)

**Direct Coolest Route** (no waypoint): 4421.5m | 55.3min | 59.6% shade

---

## Top Waypoint Recommendations

|   rank | waypoint                             |   total_dist_m |   total_time_min |   shade_pct |   shade_gain_pct |   detour_m |   detour_min |   score |
|-------:|:-------------------------------------|---------------:|-----------------:|------------:|-----------------:|-----------:|-------------:|--------:|
|      1 | Senapati Bapat Marg Midpoint         |         6343.2 |             79.3 |        58.7 |             -0.9 |     1921.7 |         24   | -0.0463 |
|      2 | Chhatrapati Sambhaji Garden Adj.     |         5527   |             69.1 |        57.2 |             -2.4 |     1105.5 |         13.8 | -0.2207 |
|      3 | Karve Nagar (Nal Stop)               |         6946.3 |             86.8 |        52   |             -7.6 |     2524.8 |         31.5 | -0.301  |
|      4 | ILS Law College Gate                 |         6859.7 |             85.7 |        48.9 |            -10.7 |     2438.2 |         30.4 | -0.4401 |
|      5 | Vishnushastri Chiplunkar Path        |         4908.5 |             61.4 |        56.5 |             -3.1 |      487   |          6.1 | -0.6386 |
|      6 | BMCC College Road                    |         4919.4 |             61.5 |        56.3 |             -3.3 |      497.9 |          6.2 | -0.6708 |
|      7 | Deccan Gymkhana                      |         4714.3 |             58.9 |        57.4 |             -2.3 |      292.8 |          3.6 | -0.7719 |
|      8 | Gopal Ganesh Agarkar Path            |         4589.2 |             57.4 |        57.7 |             -1.9 |      167.7 |          2.1 | -1.133  |
|      9 | FC Road (Wrangler P.R. Bhagwat Path) |         4915.7 |             61.4 |        53.5 |             -6.2 |      494.2 |          6.1 | -1.2465 |
|     10 | Prabhat Road (Tree Corridor)         |         5123.7 |             64   |        50.3 |             -9.3 |      702.2 |          8.7 | -1.3287 |

---

## How to Read This Table
- **shade_gain_pct**: Extra percentage of shade compared to the direct coolest route.
- **detour_m / detour_min**: Extra distance and time cost of taking the waypoint.
- **score**: Shade gain per 100m of detour — higher is a better deal.

## Interpretation

The **best waypoint** is **Senapati Bapat Marg Midpoint**:
  - Adds **+-0.9%** more shade coverage
  - Costs only **+1922 m** extra walking (24.0 extra min)
  - Shade score: 58.7% of the route is under tree/building shade

> **Day 9 Deliverables**: `day9_waypoint_recommendations.csv`, `day9_smart_planner.png`,
> `day9_smart_planner_report.md`