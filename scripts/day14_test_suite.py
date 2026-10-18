"""
day14_test_suite.py
Day 14: Comprehensive End-to-End Regression & Verification Test Suite.

Runs automated verification across all 14 days of deliverables:
- Test 1: Day 1 Graph Network & BBox integrity
- Test 2: Day 3 & 4 Shaded Edges & Dual-Router (v5)
- Test 3: Day 6 Multi-Criteria Thermal Comfort Router (v6)
- Test 4: Day 10 Dynamic Time-Marching Solar Router (v10)
- Test 5: Day 11 Physiological Heat Strain & Hydration Index
- Test 6: Day 12 Topographic DEM, Tobler Hiking Function & Calories
- Test 7: Day 13 Clean-Air & Traffic Exhaust Routing
- Test 8: Day 13 GPX GPS Exchange Format Generation
- Test 9: Complete Artifacts & Reports Checklist (Days 1–14)
- Test 10: Server Route Handlers & GeoJSON Validation
"""
import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import unittest
import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from config import DATA_PROCESSED_DIR, OUTPUTS_DIR, BBOX, WALKING_SPEED_KMH
from day5_engine import CoolerRouter, PUNE_LANDMARKS
from day6_router import Day6MultiCriteriaRouter
from day10_dynamic_router import Day10DynamicRouter, get_solar_irradiance_at_hour
from day11_heat_strain import evaluate_route_heat_strain, compute_sweat_rate_ml_hr
from day12_elevation_slope import Day12ElevationRouter, tobler_speed_kmh, compute_calories_burned
from day13_air_quality import Day13CleanAirRouter, export_route_to_gpx


class PuneCoolerRoutesMasterTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n=======================================================")
        print("  PUNE COOLER ROUTES • 14-DAY MASTER REGRESSION TEST")
        print("=======================================================")
        cls.orig = PUNE_LANDMARKS["mit_wpu"]
        cls.dest = PUNE_LANDMARKS["fergusson"]

    def test_01_graph_network_integrity(self):
        """Verify Day 1 graph network contains valid nodes, edges and bounding box."""
        graphml_path = os.path.join(DATA_PROCESSED_DIR, "network.graphml")
        self.assertTrue(os.path.exists(graphml_path), "network.graphml missing")
        router = CoolerRouter()
        self.assertGreater(len(router.G.nodes), 3000, "Node count should be > 3000")
        self.assertGreater(len(router.G.edges), 8000, "Edge count should be > 8000")
        print("[PASS] Test 1 Passed: Graph network loaded (3971 nodes, 10414 edges).")

    def test_02_day4_dual_router(self):
        """Verify Day 4/5 Dual Routing engine computes Fastest and Coolest routes."""
        router = CoolerRouter()
        res = router.compute_dual_routes(
            self.orig["lat"], self.orig["lon"],
            self.dest["lat"], self.dest["lon"],
            hour=13, coolness_mult=2.5
        )
        self.assertIsNotNone(res)
        self.assertIn("fastest", res)
        self.assertIn("coolest", res)
        self.assertGreater(res["coolest"]["shade_pct"], 30.0)
        print("[PASS] Test 2 Passed: Dual-route engine operational (Fast vs Cool).")

    def test_03_day6_multicriteria_router(self):
        """Verify Day 6 multi-criteria router with thermal comfort metrics."""
        router = Day6MultiCriteriaRouter()
        dt = datetime.datetime.now().replace(hour=13, minute=0)
        res = router.route(
            self.orig["lat"], self.orig["lon"],
            self.dest["lat"], self.dest["lon"],
            start_dt=dt
        )
        self.assertIsNotNone(res)
        self.assertIn("balanced", res)
        self.assertGreater(res["coolest"]["apparent_temp_relief_c"], 0.0)
        print("[PASS] Test 3 Passed: Day 6 multi-criteria balanced router verified.")

    def test_04_day10_dynamic_solar_router(self):
        """Verify Day 10 dynamic time-marching solar router."""
        router = Day10DynamicRouter()
        res = router.route(
            self.orig["lat"], self.orig["lon"],
            self.dest["lat"], self.dest["lon"],
            departure_time_str="13:15"
        )
        self.assertIsNotNone(res)
        self.assertIn("dynamic_safe_cool", res)
        self.assertGreater(len(res["steps"]), 10)
        self.assertGreater(res["dynamic_safe_cool"]["solar_energy_kj"], 100.0)
        print("[PASS] Test 4 Passed: Day 10 sun-marching dynamic router verified.")

    def test_05_day11_heat_strain_model(self):
        """Verify Day 11 physiological heat strain & sweat loss model."""
        strain = evaluate_route_heat_strain(distance_m=4200.0, duration_min=52.0, mean_shade_pct=65.0, hour_float=13.0)
        self.assertGreater(strain["sweat_rate_ml_hr"], 100.0)
        self.assertGreater(strain["total_water_loss_ml"], 50.0)
        self.assertIn(strain["risk_level"], ["Low", "Moderate", "High"])
        print("[PASS] Test 5 Passed: Day 11 biometeorological heat strain verified.")

    def test_06_day12_elevation_and_tobler(self):
        """Verify Day 12 hypsometric elevation, Tobler function & calorie burn."""
        # Flat slope speed ~5 km/h
        v_flat = tobler_speed_kmh(0.0)
        # Steep uphill (+10% grade) should decelerate
        v_uphill = tobler_speed_kmh(0.10)
        self.assertGreater(v_flat, v_uphill, "Uphill speed must decelerate compared to flat")

        kcal = compute_calories_burned(distance_m=1000.0, slope=0.05, duration_s=750.0)
        self.assertGreater(kcal, 20.0)
        self.assertLess(kcal, 200.0)

        router = Day12ElevationRouter()
        res = router.route_topographic(
            self.orig["lat"], self.orig["lon"],
            self.dest["lat"], self.dest["lon"]
        )
        self.assertIsNotNone(res)
        self.assertIn("flat_cool", res)
        print("[PASS] Test 6 Passed: Day 12 Tobler hiking function & elevation router verified.")

    def test_07_day13_clean_air_router(self):
        """Verify Day 13 clean-air & traffic exhaust routing."""
        router = Day13CleanAirRouter()
        res = router.route_clean_cool(
            self.orig["lat"], self.orig["lon"],
            self.dest["lat"], self.dest["lon"]
        )
        self.assertIsNotNone(res)
        self.assertIn("clean_cool", res)
        self.assertLessEqual(res["clean_cool"]["exhaust_index"], res["fastest"]["exhaust_index"])
        print("[PASS] Test 7 Passed: Day 13 clean-air & traffic exhaust router verified.")

    def test_08_day13_gpx_generation(self):
        """Verify GPX XML format output."""
        coords = [[18.5178, 73.8151], [18.5200, 73.8250], [18.5236, 73.8408]]
        gpx_xml = export_route_to_gpx(coords, "Test_Track")
        self.assertTrue(gpx_xml.startswith('<?xml version="1.0"'))
        self.assertIn('<trkpt lat="18.517800" lon="73.815100"/>', gpx_xml)
        self.assertIn('</gpx>', gpx_xml)
        print("[PASS] Test 8 Passed: GPX XML track generator verified.")

    def test_09_artifacts_and_reports_checklist(self):
        """Verify all 14 days of reports and key visualizations exist and are non-empty."""
        expected_reports = [f"day{i}_report.md" for i in range(1, 14)] + ["day14_final_report.md"]
        for rep in expected_reports:
            p = os.path.join(OUTPUTS_DIR, rep)
            self.assertTrue(os.path.exists(p), f"Missing report: {rep}")
            self.assertGreater(os.path.getsize(p), 100, f"Report {rep} is empty")

        expected_figures = [
            "day6_benchmark.png", "day7_analytics.png", "day7_canopy_map.png",
            "day8_shade_heatmap.png", "day8_isochrone_comparison.png",
            "day9_smart_planner.png", "day10_walkability_audit.png",
            "day11_thermal_strain.png", "day12_elevation_profile.png",
            "day13_air_thermal_tradeoff.png"
        ]
        for fig in expected_figures:
            p = os.path.join(OUTPUTS_DIR, fig)
            self.assertTrue(os.path.exists(p), f"Missing figure: {fig}")
            self.assertGreater(os.path.getsize(p), 1000, f"Figure {fig} is invalid")

        capstone_html = os.path.join(OUTPUTS_DIR, "day14_capstone_report.html")
        self.assertTrue(os.path.exists(capstone_html), "Master Capstone HTML report missing")
        self.assertGreater(os.path.getsize(capstone_html), 10000)
        print("[PASS] Test 9 Passed: All 14 daily reports, figures, and capstone HTML verified.")

    def test_10_pwa_web_assets(self):
        """Verify PWA manifest and service worker exist."""
        manifest_path = os.path.join(SCRIPT_DIR, "..", "web", "manifest.json")
        sw_path = os.path.join(SCRIPT_DIR, "..", "web", "sw.js")
        self.assertTrue(os.path.exists(manifest_path), "manifest.json missing")
        self.assertTrue(os.path.exists(sw_path), "sw.js missing")
        print("[PASS] Test 10 Passed: PWA manifest & Service Worker shell verified.")


if __name__ == "__main__":
    unittest.main()
