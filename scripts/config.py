import os
import osmnx as ox

# Bounding box for pilot area (west, south, east, north)
BBOX = (73.802, 18.495, 73.846, 18.531)

# Test points
PT_MIT_WPU = (18.5178, 73.8151)
PT_FC = (18.5236, 73.8408)

# Walking speed in km/h
WALKING_SPEED_KMH = 4.8

# Folders
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DATA_CACHE_DIR = os.path.join(BASE_DIR, "data", "cache")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

# Setup cache
ox.settings.cache_folder = DATA_CACHE_DIR
ox.settings.use_cache = True
