import bpy
import csv
import os
from math import radians, cos
from mathutils import Vector


csv_directory_path = ""
csv_file_path_mercator = ""


LATITUDE_SCALE = 111320  
LONGITUDE_SCALE = 111320  # Meters per degree of longitude (approximation at the equator)


def safe_float_conversion(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def calculate_average_latitude_from_directory(directory_path):
    latitudes = []
    for filename in os.listdir(directory_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(directory_path, filename)
            latitudes.extend(calculate_latitudes_from_file(file_path))
    return sum(latitudes) / len(latitudes) if latitudes else 0

def calculate_latitudes_from_file(filepath):
    latitudes = []
    with open(filepath, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            lat = safe_float_conversion(row.get('latitude'))
            if lat is not None:
                latitudes.append(lat)
    return latitudes


reference_latitude = calculate_average_latitude_from_directory(csv_directory_path)
print(f"Reference Latitude: {reference_latitude}")

# Conversion factors
lon_to_meters = LONGITUDE_SCALE * cos(radians(reference_latitude))

# Convert latitude and longitude to Cartesian coordinates (Mercator)
def lat_lon_to_cartesian(latitude, longitude, z=0):
    x = longitude * lon_to_meters
    y = latitude * LATITUDE_SCALE
    return Vector((x, y, -abs(z)))  # Ensure z is always negative

# Function to create empty points from Mercator CSV
def add_empty_point(name, location, metadata):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (1, 1, 1)
    for key, value in metadata.items():
        if value is not None:
            obj[key] = value

def import_mercator_csv(filepath):
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            pt = row.get('pt')
            b_value = row.get('B')
            month = row.get('month')
            longitude = safe_float_conversion(row.get('longitude'))
            latitude = safe_float_conversion(row.get('latitude'))
            z = safe_float_conversion(row.get('z'))
            datum = row.get('Datum')

            if z is None:
                z = 0

            if longitude is not None and latitude is not None:
                location = lat_lon_to_cartesian(latitude, longitude, z)
                mud_data = {key: safe_float_conversion(row.get(key)) for key in row if key.startswith('mud_')}
                wat_data = {key: safe_float_conversion(row.get(key)) for key in row if key.startswith('wat_')}
                metadata = {'Datum': datum, **mud_data, **wat_data}

                point_name = f"B{b_value}_pt{pt}_month{month}"
                print(f"Adding point: {point_name} at {location} with metadata {metadata}")
                add_empty_point(point_name, location, metadata)
            else:
                print(f"Skipping row due to missing longitude, latitude, or z: {row}")

def create_point_cloud_from_csv(filepath):
    points = []

    with open(filepath, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                lat = safe_float_conversion(row.get('latitude'))
                lon = safe_float_conversion(row.get('longitude'))
                z = safe_float_conversion(row.get('z'))

                if z is None:
                    z = 0

                if lat is not None and lon is not None:
                    point = lat_lon_to_cartesian(lat, lon, z)
                    points.append(point)
                else:
                    print(f"Skipping row due to missing or invalid data: {row}")
            except Exception as e:
                print(f"Error processing row: {row}, error: {e}")

    if not points:
        print("No valid points to display.")
        return


    mesh = bpy.data.meshes.new(name=os.path.basename(filepath).replace('.csv', '_PointCloud'))
    obj = bpy.data.objects.new(name=mesh.name, object_data=mesh)
    bpy.context.collection.objects.link(obj)

    vertices = [point for point in points]
    mesh.from_pydata(vertices, [], [])
    mesh.update()

    mat = bpy.data.materials.new(name="PointCloudMaterial")
    mat.diffuse_color = (0, 1, 0, 1) 
    obj.data.materials.append(mat)

print("Importing points from Mercator CSV...")
import_mercator_csv(csv_file_path_mercator)

print("Processing point clouds from directory...")

for filename in os.listdir(csv_directory_path):
    if filename.endswith(".csv"):
        file_path = os.path.join(csv_directory_path, filename)
        print(f"Processing file: {file_path}")
        create_point_cloud_from_csv(file_path)

print("Point clouds created from all CSV files.")
