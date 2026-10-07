# Pune Cooler Routes - Day 4 Report

## What We Built
A dual-route engine computing two walking paths from MIT-WPU to Fergusson College:
- **Fastest Route**: Dijkstra on raw edge length.
- **Coolest Route**: Dijkstra on cool_weight (shade-inflated cost + road safety penalty).

## Loophole Fixes Applied
1. **Dynamic Time**: Picks shade snapshot nearest to current hour (22:00).
2. **Sidewalk Safety**: motorway/trunk edges get a 3x cost penalty.
3. **Tree Canopies**: included in shadow casting from Day 3.

## Results (run at 22:54 IST)

| | Fastest | Coolest |
|---|---|---|
| Distance | 4339.0 m | 4339.0 m |
| Walking Time | 54.2 min | 54.2 min |
| Avg Shade | 10.4% | 10.4% |

**Tradeoff**: Coolest adds 0.0 m (0.0 min) but gains 0.0% more shade.

## Output Files
- `outputs/routes_day4.geojson` - both routes ready for web map display.
