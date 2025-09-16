import os
import time
import requests
import folium
import googlemaps
from dotenv import load_dotenv

load_dotenv()
GMAPS_API_KEY = os.getenv('MAPS_API_KEY')

# --- Monkey patch requests for local testing ---
_old_request_get = requests.get
def _patched_get(*args, **kwargs):
    kwargs['verify'] = False
    return _old_request_get(*args, **kwargs)
requests.get = _patched_get

gmaps = googlemaps.Client(key=GMAPS_API_KEY)


def find_closest_available_ambulance(patient_location, fleet, driver_status):
    closest_ambulance = None
    best_route = None
    shortest_duration = float('inf')

    for ambulance in fleet:
        status = driver_status.get(ambulance['username'], {'on_duty': True, 'assigned': False})
        if not status.get('on_duty') or status.get('assigned'):
            continue  # Skip unavailable drivers

        origin = f"{ambulance['location'][0]},{ambulance['location'][1]}"
        destination = f"{patient_location[0]},{patient_location[1]}"

        try:
            directions_result = gmaps.directions(
                origin, destination, mode="driving",
                departure_time=int(time.time()), traffic_model='best_guess'
            )
            if directions_result:
                duration = directions_result[0]['legs'][0]['duration_in_traffic']['value']
                if duration < shortest_duration:
                    shortest_duration = duration
                    closest_ambulance = ambulance
                    best_route = directions_result[0]
        except Exception as e:
            print(f"Error fetching route for ambulance {ambulance['name']}: {e}")
            continue

    return closest_ambulance, best_route


def find_closest_hospital_gmaps(patient_location, hospitals):
    closest_hospital = None
    best_route = None
    shortest_duration = float('inf')

    for hospital in hospitals:
        origin = f"{patient_location[0]},{patient_location[1]}"
        destination = f"{hospital['location'][0]},{hospital['location'][1]}"

        try:
            directions_result = gmaps.directions(
                origin, destination, mode="driving",
                departure_time=int(time.time()), traffic_model='best_guess'
            )
            if directions_result:
                duration = directions_result[0]['legs'][0]['duration_in_traffic']['value']
                if duration < shortest_duration:
                    shortest_duration = duration
                    closest_hospital = hospital
                    best_route = directions_result[0]
        except Exception as e:
            print(f"Error fetching route to hospital {hospital['name']}: {e}")
            continue

    return closest_hospital, best_route


def draw_route(origin, destination, folium_map, color='blue'):
    directions = gmaps.directions(
        origin=f"{origin[0]},{origin[1]}",
        destination=f"{destination[0]},{destination[1]}",
        mode="driving",
        departure_time="now",
        traffic_model="best_guess"
    )
    if directions:
        steps = directions[0]['legs'][0]['steps']
        for step in steps:
            polyline = step['polyline']['points']
            coords = [(p['lat'], p['lng']) for p in googlemaps.convert.decode_polyline(polyline)]
            folium.PolyLine(coords, color=color, weight=5, opacity=0.7).add_to(folium_map)


def run_simulation_gmaps(patient_location, selected_type='private', driver_status=None, api_key=GMAPS_API_KEY):
    if driver_status is None:
        driver_status = {}

    # --- Fleet Setup ---
    private_fleet = [
        {"id": 1, "name": "Ambulance Secunderabad Station", "location": (17.4360, 78.5020), "username": "secunderabad_driver", "type": "private"},
        {"id": 2, "name": "Ambulance Nampally", "location": (17.3915, 78.4633), "username": "nampally_driver", "type": "private"},
        {"id": 5, "name": "Ambulance Hitec City", "location": (17.4474, 78.3762), "username": "hitec_driver", "type": "private"},
        {"id": 6, "name": "Ambulance Gachibowli", "location": (17.4401, 78.3489), "username": "gachibowli_driver", "type": "private"},
    ]
    govt_fleet = [
        {"id": 3, "name": "Ambulance Banjara Hills", "location": (17.4148, 78.4418), "username": "banjara_driver", "type": "government"},
        {"id": 4, "name": "Ambulance Ameerpet", "location": (17.4375, 78.4483), "username": "ameerpet_driver", "type": "government"},
        {"id": 7, "name": "Ambulance Kukatpally (KPHB)", "location": (17.4848, 78.4138), "username": "kukatpally_driver", "type": "government"},
        {"id": 8, "name": "Ambulance Madhapur", "location": (17.4504, 78.3973), "username": "madhapur_driver", "type": "government"},
    ]
    hospitals = [
        {"name": "Osmania General Hospital", "location": (17.3753, 78.4747)},
        {"name": "Apollo Hospitals, Jubilee Hills", "location": (17.4202, 78.4013)},
    ]

    fleet = private_fleet if selected_type == 'private' else govt_fleet

    # --- Find closest available ambulance ---
    ambulance, _ = find_closest_available_ambulance(patient_location, fleet, driver_status)
    if not ambulance:
        return {"status": "waiting"}  # no driver available

    # Mark as assigned in driver_status
    driver_status.setdefault(ambulance['username'], {'on_duty': True, 'assigned': False})
    driver_status[ambulance['username']]['assigned'] = True
    ambulance['available'] = False

    # Find closest hospital
    hospital, _ = find_closest_hospital_gmaps(patient_location, hospitals)

    # --- Folium Map ---
    m = folium.Map(location=patient_location, zoom_start=13)
    folium.Marker(location=patient_location, popup="🧍‍♂ Patient", icon=folium.Icon(color='red', icon='user', prefix='fa')).add_to(m)
    folium.Marker(location=hospital['location'], popup=f"🏥 {hospital['name']}", icon=folium.Icon(color='orange', icon='plus', prefix='fa')).add_to(m)
    folium.Marker(location=ambulance['location'], popup=f"🚑 {ambulance['name']} - Waiting for driver",
                  icon=folium.Icon(color='gray', icon='ambulance', prefix='fa')).add_to(m)
    draw_route(ambulance['location'], patient_location, m, color='blue')
    draw_route(patient_location, hospital['location'], m, color='red')
    m.save("static/ambulance_dispatch_map.html")

    return {
        "status": "waiting",
        "ambulance": {"username": ambulance['username'], "name": ambulance['name'], "status": "waiting"},
        "hospital": {"name": hospital['name']},
        "patient_location": patient_location
    }
