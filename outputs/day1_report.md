# Pune Cooler Routes - Day 1 Report

## Software Versions
* Python: 3.13.5
* OSMnx: 2.1.1
* scikit-learn: 1.9.1
* matplotlib: 3.11.2
* scipy: 1.18.1
* geopandas: 1.2.0

## Network Counts
* **Initial Network**: 4056 nodes, 10530 edges
* **Total Length**: 638.43 km
* **Dropped Nodes**: 85 nodes were removed to keep only the largest connected component.

## Route Results (MIT-WPU to Fergusson College)
* **Geocode Verifications**:
  * MIT-WPU differed by 82.9 m from the user coordinates.
  * Fergusson College differed by 240.7 m from the user coordinates.
* **Snap Distances**:
  * MIT-WPU snapped to a node 154.3 m away.
  * Fergusson College snapped to a node 61.9 m away.
* **Shortest Route**:
  * Distance: 4339.0 m
  * Walking time: 54.2 minutes (at 4.8 km/h)
  * Number of segments: 58
  * Street names: Admiral Somnath Path, ARAI Road, Kanchangalli to Hanuman Temple, Kanchan Gully, Vishnushastri Chiplunkar Path, Bhandarkar Path, Gopal Ganesh Agarkar Path, Off FC Road, Keshav Ramchandra Kanitkar Path, Gopal Krushna Gokhale Path.
* **Robustness**: 20 out of 20 random node pair routes succeeded.

## Sidewalk Audit Summary
**All Motor Roads**
* footway nearby: 1090 segments (31.3 km)
* sidewalk tagged: 48 segments (5.5 km)
* unknown: 6950 segments (463.7 km)

**Primary, Secondary & Tertiary Roads Only**
* footway nearby: 860 segments (25.7 km)
* sidewalk tagged: 48 segments (5.5 km)
* unknown: 2194 segments (142.5 km)

### Top 10 Sidewalk Gaps (Main Roads)
1. unnamed (highway=tertiary): 17.2 km
2. Paud Road (primary): 10.3 km
3. Karve Road (primary): 9.9 km
4. Gulwani Maharaj Path (tertiary): 4.5 km
5. Sinhagad Road (primary): 4.3 km
6. Raja Mantri Path (secondary): 4.1 km
7. Pu. Bha. Bhave Path (tertiary): 3.8 km
8. Vishnushastri Chiplunkar Path (primary): 3.7 km
9. DP Road (secondary): 3.3 km
10. Rambaug Colony Road (tertiary): 3.2 km

## Issues and Skipped Items
* **pybdshadow `keplergl` warning**: As expected, `keplergl` failed to install during dependency resolution for `pybdshadow` on Python 3.13, which printed an error in the pip logs. The package itself was imported successfully.
* **Shade mapping skipped**: We did not map shade, trees, or covered sections today as planned.

## Risks for Day 2 (Building Heights)
1. **Missing height data in Open Buildings V3**: Many buildings in Pune might lack height values in the dataset, requiring a fallback interpolation or masking (e.g. 6 m default).
2. **Date alignment**: Heights can change between years (2.5D Temporal data ranges from 2016 to 2023). Mismatches between satellite imagery used for tree shading and building age might cause shade calculation inaccuracies.
3. **Accuracy of low-confidence pixels**: We may incorrectly flag some pixels as "no height" or use false heights where confidence is low, leading to inaccurate building shadow lengths in the morning/evening.
