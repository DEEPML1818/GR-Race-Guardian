import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Attempting to import get_track_coordinates...")
    from grracing.track_coordinates import get_track_coordinates
    print("Import successful.")
    
    print("Instantiating TrackCoordinates...")
    coords_manager = get_track_coordinates()
    print("Instantiation successful.")
    
    print("Getting coordinates for 'barber'...")
    track_data = coords_manager.get_track_coordinates('barber')
    print(f"Got data keys: {track_data.keys()}")
    
    if "coordinates" in track_data:
        print(f"Number of points: {len(track_data['coordinates'])}")
        first_point = track_data['coordinates'][0]
        print(f"First point: {first_point}")
        
        # Test path generation logic
        points = track_data["coordinates"]
        path = f"M {points[0]['x']*1000} {points[0]['y']*1000}"
        for p in points[1:]:
            path += f" L {p['x']*1000} {p['y']*1000}"
        path += " Z"
        print(f"Generated path length: {len(path)}")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
