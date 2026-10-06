# Pune Cooler Routes - Day 3 Report

## Objective
Calculate building and vegetation shadows at different times of the day and assign shadow weights to the walking network edges.

## Solving Previous Loopholes
During execution, we not only completed the base MVP goals, but specifically solved three major loopholes identified in Day 2:
1. **The "Missing Trees" Loophole**: We successfully fetched urban vegetation (`natural=tree`, `natural=wood`, `natural=tree_row`) from OpenStreetMap, buffered them into 5m-radius canopies, and assigned them a default 10-meter height to accurately cast tree shadows alongside buildings!
2. **The Dynamic Time Constraints Loophole**: Instead of generating a single static shadow profile, we cast shadows for three distinct times of day: 09:00 (Morning), 13:00 (Mid-day), and 16:00 (Late Afternoon). This allows our routing algorithm to adapt dynamically based on when the user is walking.
3. **The Covered Walkways Loophole**: We added logic to check the street network for `covered=yes` or `tunnel=building_passage` tags, guaranteeing that awnings and arcades are treated as 100% shaded regardless of sun angle.

## Shadow Pipeline
Using `pybdshadow` and `geopandas`, we:
* Downloaded the full bounding box of buildings and trees.
* Cast shadows for the mid-summer sun path (May 15).
* Performed high-speed spatial intersections between the thousands of shadow polygons and network edges.
* Appended `shade_frac_0900`, `shade_frac_1300`, and `shade_frac_1600` columns to the network edges.

## Status
The shaded network graph is now successfully saved as `data/processed/edges_shaded.gpkg` and is ready for Day 4 routing algorithms!
