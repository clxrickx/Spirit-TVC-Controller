import bpy
import csv
import math
from mathutils import Vector, Euler, Matrix

CSV_PATH = "/Users/christophercyhui/Documents/engineering/test3.csv" 
FPS = 30
SCALE = 1.0
print("\n--- STARTING OPENROCKET IMPORT ---")

try:
    with open(CSV_PATH, mode='r', encoding='utf-8') as f:
        raw_lines = f.readlines()
except Exception as e:
    print(f"CRITICAL ERROR reading file: {e}")
    raw_lines = []

clean_lines = []
for line in raw_lines:
    stripped = line.strip()
    # If the line starts with # but contains comma separators then it's the header row
    if stripped.startswith('#') and ',' in stripped:
        clean_lines.append(stripped.lstrip('#').strip())
    # Standard non-comment data lines
    elif not stripped.startswith('#') and len(stripped) > 0:
        clean_lines.append(stripped)

if not clean_lines:
    print("CSV-ERROR: No valid data lines found in CSV.")
else:
    reader = csv.DictReader(clean_lines)
    
    # Clean up column headers (strip quotes/spaces)
    headers = [h.strip().replace('"', '') for h in reader.fieldnames] if reader.fieldnames else []
    print(f"Detected CSV Headers: {headers}")

    # Auto-match column names dynamically
    time_col = next((h for h in headers if "time" in h.lower()), None)
    alt_col = next((h for h in headers if "altitude" in h.lower()), None)
    north_col = next((h for h in headers if "north" in h.lower()), None)
    east_col = next((h for h in headers if "east" in h.lower()), None)
    zenith_col = next((h for h in headers if "zenith" in h.lower() or "vertical orientation" in h.lower()), None)
    azimuth_col = next((h for h in headers if "azimuth" in h.lower() or "lateral orientation" in h.lower()), None)

    print(f"Matched Columns -> Time: '{time_col}', Alt: '{alt_col}', Zenith: '{zenith_col}'")

    if not time_col or not alt_col:
        print("ERROR: Could not find required 'Time' or 'Altitude' headers in CSV.")
    else:

        rocket_obj = bpy.data.objects.get("Rocket")
        if not rocket_obj: # backup if the object doesn't exist, create a simple cylinder to represent the rocket
            bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=2.0, location=(0, 0, 1))
            rocket_obj = bpy.context.active_object
            rocket_obj.name = "Rocket"
        rocket_obj.animation_data_clear()

        rows_imported = 0
        first_time = None

        for row in reader:
            # Clean dictionary keys/values
            clean_row = {k.strip().replace('"', ''): v.strip() for k, v in row.items() if k}
            
            try:
                time_val = float(clean_row[time_col])
                alt = float(clean_row[alt_col]) * SCALE
                north = float(clean_row[north_col]) * SCALE if north_col else 0.0
                east = float(clean_row[east_col]) * SCALE if east_col else 0.0
                zenith = float(clean_row[zenith_col]) if zenith_col else 0.0
                azimuth = float(clean_row[azimuth_col]) if azimuth_col else 0.0
            except (ValueError, KeyError):
                continue
            
            # FIX 1: Set base start time on first valid row
            if first_time is None:
                first_time = time_val

            frame = int((time_val - first_time) * FPS) + 1

            # FIX 2: Convert angles to radians
            pitch_rad = math.radians(zenith)    # 0° = vertical up
            azimuth_rad = math.radians(azimuth) # 0° = North (+Y), 90° = East (+X)

            # Construct Euler rotation directly (Z-X-Y order)
            rocket_euler = Euler((pitch_rad, 0.0, -azimuth_rad), 'ZXY')

            # Apply location and explicit Euler rotation
            rocket_obj.location = (east, north, alt)
            rocket_obj.rotation_euler = rocket_euler

            # Insert keyframes
            rocket_obj.keyframe_insert(data_path="location", frame=frame)
            rocket_obj.keyframe_insert(data_path="rotation_euler", frame=frame)

            rows_imported += 1
            bpy.context.scene.frame_end = frame

        print(f"SUCCESS: Imported {rows_imported} keyframe rows into Blender!")