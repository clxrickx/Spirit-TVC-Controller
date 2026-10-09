import bpy
import csv
import math
from mathutils import Vector, Quaternion

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
    if stripped.startswith('#') and ',' in stripped:
        clean_lines.append(stripped.lstrip('#').strip())
    elif not stripped.startswith('#') and len(stripped) > 0:
        clean_lines.append(stripped)

if not clean_lines:
    print("CSV-ERROR: No valid data lines found in CSV.")
else:
    reader = csv.DictReader(clean_lines)
    
    headers = [h.strip().replace('"', '') for h in reader.fieldnames] if reader.fieldnames else []
    print(f"Detected CSV Headers: {headers}")

    time_col = next((h for h in headers if "time" in h.lower()), None)
    alt_col = next((h for h in headers if "altitude" in h.lower()), None)
    north_col = next((h for h in headers if "north" in h.lower()), None)
    east_col = next((h for h in headers if "east" in h.lower()), None)
    zenith_col = next((h for h in headers if "zenith" in h.lower() or "vertical orientation" in h.lower()), None)
    azimuth_col = next((h for h in headers if "azimuth" in h.lower() or "lateral orientation" in h.lower()), None)

    if not time_col or not alt_col:
        print("ERROR: Could not find required 'Time' or 'Altitude' headers in CSV.")
    else:

        rocket_obj = bpy.data.objects.get("Rocket")
        if not rocket_obj:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=2.0, location=(0, 0, 1))
            rocket_obj = bpy.context.active_object
            rocket_obj.name = "Rocket"
        
        # Set Blender rotation mode to Quaternion
        rocket_obj.rotation_mode = 'QUATERNION'
        rocket_obj.animation_data_clear()

        rows_imported = 0
        first_time = None
        up_vec = Vector((0, 0, 1))

        for row in reader:
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
            
            if first_time is None:
                first_time = time_val

            frame = int((time_val - first_time) * FPS) + 1

            pitch_rad = math.radians(zenith)
            azimuth_rad = math.radians(azimuth)

            # Compute actual 3D pointing direction vector
            # When zenith is near 0, dir_x and dir_y are ~0, dir_z is ~1.0
            dir_x = math.sin(pitch_rad) * math.sin(azimuth_rad)
            dir_y = math.sin(pitch_rad) * math.cos(azimuth_rad)
            dir_z = math.cos(pitch_rad)
            
            pointing_dir = Vector((dir_x, dir_y, dir_z))

            # If rocket is practically vertical, default to pure straight-up quaternion
            if pointing_dir.length < 1e-4 or zenith < 0.01:
                quat = Quaternion((1.0, 0.0, 0.0, 0.0))
            else:
                pointing_dir.normalize()
                # Compute smooth Quaternion rotation from +Z up to pointing_dir
                quat = up_vec.rotation_difference(pointing_dir)

            # Apply location and Quaternion rotation
            rocket_obj.location = (east, north, alt)
            rocket_obj.rotation_quaternion = quat

            # Keyframe location and rotation_quaternion
            rocket_obj.keyframe_insert(data_path="location", frame=frame)
            rocket_obj.keyframe_insert(data_path="rotation_quaternion", frame=frame)

            rows_imported += 1
            bpy.context.scene.frame_end = frame

        print(f"SUCCESS: Imported {rows_imported} keyframe rows using Quaternions!")