"""
Extract real GPS coordinates for race tracks from OpenStreetMap.
This creates accurate track paths by querying the Overpass API.
"""

import requests
import json
import time

def get_track_from_osm(track_name, osm_way_id=None, osm_relation_id=None):
    """
    Extract track coordinates from OpenStreetMap using Overpass API.
    
    Args:
        track_name: Name of the track
        osm_way_id: OpenStreetMap way ID (if known)
        osm_relation_id: OpenStreetMap relation ID (if known)
    
    Returns:
        List of [lat, lon] coordinates
    """
    
    # Overpass API endpoint
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Build query based on what we have
    if osm_way_id:
        query = f"""
        [out:json];
        way({osm_way_id});
        out geom;
        """
    elif osm_relation_id:
        query = f"""
        [out:json];
        relation({osm_relation_id});
        out geom;
        """
    else:
        # Search by name
        query = f"""
        [out:json];
        (
          way["name"~"{track_name}"]["sport"="motor"];
          relation["name"~"{track_name}"]["sport"="motor"];
        );
        out geom;
        """
    
    try:
        response = requests.post(overpass_url, data={'data': query})
        data = response.json()
        
        if not data.get('elements'):
            print(f"No data found for {track_name}")
            return []
        
        # Extract coordinates
        coords = []
        for element in data['elements']:
            if element['type'] == 'way':
                if 'geometry' in element:
                    coords = [[node['lat'], node['lon']] for node in element['geometry']]
                elif 'nodes' in element:
                    coords = [[node['lat'], node['lon']] for node in element['nodes']]
            elif element['type'] == 'relation':
                # For relations, get all member ways
                for member in element.get('members', []):
                    if member['type'] == 'way' and 'geometry' in member:
                        coords.extend([[node['lat'], node['lon']] for node in member['geometry']])
        
        return coords
    
    except Exception as e:
        print(f"Error fetching {track_name}: {e}")
        return []


# Known OpenStreetMap IDs for race tracks
TRACK_OSM_IDS = {
    "cota": {
        "name": "Circuit of the Americas",
        "way_id": 172286064,  # Main circuit way
    },
    "barber": {
        "name": "Barber Motorsports Park",
        "way_id": 138524916,
    },
    "indianapolis": {
        "name": "Indianapolis Motor Speedway",
        "relation_id": 1933690,  # Road course
    },
    "road-america": {
        "name": "Road America",
        "way_id": 27553959,
    },
    "sebring": {
        "name": "Sebring International Raceway",
        "way_id": 161445853,
    },
    "sonoma": {
        "name": "Sonoma Raceway",
        "way_id": 30262537,
    },
    "vir": {
        "name": "Virginia International Raceway",
        "way_id": 138525011,
    },
    "laguna-seca": {
        "name": "WeatherTech Raceway Laguna Seca",
        "way_id": 27553960,
    }
}


def extract_all_tracks():
    """Extract GPS coordinates for all tracks."""
    
    all_tracks = {}
    
    for track_id, info in TRACK_OSM_IDS.items():
        print(f"\nExtracting {info['name']}...")
        
        coords = get_track_from_osm(
            info['name'],
            osm_way_id=info.get('way_id'),
            osm_relation_id=info.get('relation_id')
        )
        
        if coords:
            all_tracks[track_id] = {
                "name": info['name'],
                "track_path": coords,
                "num_points": len(coords)
            }
            print(f"  [OK] Got {len(coords)} points")
        else:
            print(f"  [FAIL] Failed to get coordinates")
        
        # Be nice to the API
        time.sleep(1)
    
    # Save to JSON
    output_file = "real_track_gps_coordinates.json"
    with open(output_file, 'w') as f:
        json.dump(all_tracks, f, indent=2)
    
    print(f"\n[OK] Saved to {output_file}")
    return all_tracks


if __name__ == "__main__":
    print("Extracting real GPS coordinates from OpenStreetMap...")
    print("This may take a minute...")
    tracks = extract_all_tracks()
    
    print(f"\nExtracted {len(tracks)} tracks:")
    for track_id, data in tracks.items():
        print(f"  - {data['name']}: {data['num_points']} GPS points")
