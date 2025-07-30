import osmnx as ox
import networkx as nx
import folium
import googlemaps
import time
import requests

# Initialize Google Maps client
GMAPS_API_KEY = 'AIzaSyCfGUtxuviXpo2G9kRdyp8-8loCkR8rxsA'
gmaps = googlemaps.Client(key=GMAPS_API_KEY)

def find_closest_ambulance_gmaps(patient_location, fleet):
    closest_ambulance = None
    best_route = None
    shortest_duration = float('inf')

    for ambulance in fleet:
        origin = f"{ambulance['location'][0]},{ambulance['location'][1]}"
        destination = f"{patient_location[0]},{patient_location[1]}"
        try:
            directions_result = gmaps.directions(origin, destination, mode="driving", departure_time=int(time.time()), traffic_model='best_guess')
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
            directions_result = gmaps.directions(origin, destination, mode="driving", departure_time=int(time.time()), traffic_model='best_guess')
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

def draw_google_route_on_map(route, folium_map, color='blue'):
    steps = route['legs'][0]['steps']
    for step in steps:
        polyline = step['polyline']['points']
        decoded = googlemaps.convert.decode_polyline(polyline)
        points = [(point['lat'], point['lng']) for point in decoded]
        folium.PolyLine(points, color=color, weight=5, opacity=0.8).add_to(folium_map)

def get_distance_and_time_from_google(origin_coords, destination_coords, api_key):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{origin_coords[0]},{origin_coords[1]}",
        "destination": f"{destination_coords[0]},{destination_coords[1]}",
        "key": api_key,
        "departure_time": "now"
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data["status"] == "OK":
        leg = data["routes"][0]["legs"][0]
        distance_text = leg["distance"]["text"]
        duration_text = leg["duration"]["text"]
        duration_in_traffic = leg.get("duration_in_traffic", {}).get("text", duration_text)
        return distance_text, duration_in_traffic
    else:
        print("❌ Error:", data["status"])
        return None, None

def run_simulation_gmaps(patient_location, api_key):
    fleet = [
        # Central Zone
        {"id": 1, "name": "Ambulance Secunderabad Station", "location": (17.4360, 78.5020), "username": "secunderabad_driver"},
        {"id": 2, "name": "Ambulance Nampally", "location": (17.3915, 78.4633), "username": "nampally_driver"},
        {"id": 3, "name": "Ambulance Banjara Hills", "location": (17.4148, 78.4418), "username": "banjara_driver"},
        {"id": 4, "name": "Ambulance Ameerpet", "location": (17.4375, 78.4483), "username": "ameerpet_driver"},
        # West Zone
        {"id": 5, "name": "Ambulance Hitec City", "location": (17.4474, 78.3762), "username": "hitec_driver"},
        {"id": 6, "name": "Ambulance Gachibowli", "location": (17.4401, 78.3489), "username": "gachibowli_driver"},
        {"id": 7, "name": "Ambulance Kukatpally (KPHB)", "location": (17.4848, 78.4138), "username": "kukatpally_driver"},
        {"id": 8, "name": "Ambulance Madhapur", "location": (17.4504, 78.3973), "username": "madhapur_driver"},
        # East Zone
        {"id": 9, "name": "Ambulance Uppal", "location": (17.4162, 78.5632), "username": "uppal_driver"},
        {"id": 10, "name": "Ambulance LB Nagar", "location": (17.3523, 78.5523), "username": "lbnagar_driver"},
        {"id": 11, "name": "Ambulance Tarnaka", "location": (17.4310, 78.5312), "username": "tarnaka_driver"},
        {"id": 12, "name": "Ambulance Dilsukhnagar", "location": (17.3688, 78.5247), "username": "dilsukhnagar_driver"},
        # North Zone
        {"id": 13, "name": "Ambulance Kompally", "location": (17.5401, 78.4981), "username": "kompally_driver"},
        {"id": 14, "name": "Ambulance Alwal", "location": (17.5188, 78.5085), "username": "alwal_driver"},
        {"id": 15, "name": "Ambulance Bowenpally", "location": (17.4811, 78.4878), "username": "bowenpally_driver"},
        {"id": 16, "name": "Ambulance Jeedimetla", "location": (17.5215, 78.4686), "username": "jeedimetla_driver"},
        # South Zone
        {"id": 17, "name": "Ambulance Charminar", "location": (17.3616, 78.4747), "username": "charminar_driver"},
        {"id": 18, "name": "Ambulance Airport Zone (Shamshabad)", "location": (17.2403, 78.4294), "username": "shamshabad_driver"},
        {"id": 19, "name": "Ambulance Mehdipatnam", "location": (17.3912, 78.4458), "username": "mehdipatnam_driver"},
        {"id": 20, "name": "Ambulance Falaknuma", "location": (17.3331, 78.4689), "username": "falaknuma_driver"},
        # Narsapur Entry
        
        
    ]

    hospitals = [
        {"name": "Osmania General Hospital", "location": (17.3753, 78.4747)},
        {"name": "Apollo Hospitals, Jubilee Hills", "location": (17.4202, 78.4013)},
        {"name": "NIMS, Panjagutta", "location": (17.4239, 78.4580)},
        {"name": "Gandhi Hospital, Secunderabad", "location": (17.4351, 78.4984)},
        {"name": "KIMS Hospitals, Secunderabad", "location": (17.4430, 78.5197)},
        {"name": "Yashoda Hospitals, Somajiguda", "location": (17.4214, 78.4602)},
        {"name": "Continental Hospitals, Gachibowli", "location": (17.4172, 78.3444)},
        {"name": "Sunshine Hospitals, Gachibowli", "location": (17.4435, 78.3623)},
        {"name": "Care Hospitals, Banjara Hills", "location": (17.4158, 78.4488)},
        {"name": "Medicover Hospitals, Hitec City", "location": (17.4519, 78.3871)},
        # Narsapur Entry with a comma added before it
         
    ]

    closest_amb, amb_route = find_closest_ambulance_gmaps(patient_location, fleet)
    closest_hosp, hosp_route = find_closest_hospital_gmaps(patient_location, hospitals)

    if not closest_amb or not closest_hosp:
        print("❌ Could not find a suitable ambulance or hospital.")
        return None

    amb_dist, amb_time = get_distance_and_time_from_google(closest_amb['location'], patient_location, api_key)
    hosp_dist, hosp_time = get_distance_and_time_from_google(patient_location, closest_hosp['location'], api_key)

    if not amb_route or not hosp_route:
        print("❌ No suitable route found.")
        return None

    m = folium.Map(location=patient_location, zoom_start=13)

    folium.Marker(
        location=patient_location,
        popup="🧍‍♂ Patient 📍",
        icon=folium.Icon(color='red', icon='plus-sign')
    ).add_to(m)

    for amb in fleet:
        icon_color = 'green' if amb['id'] == closest_amb['id'] else 'blue'
        popup_text = amb['name']
        if amb['id'] == closest_amb['id']:
             popup_text = f"🚑 <b>{amb['name']}</b><br>📏 Distance: <b>{amb_dist}</b><br>⏱ ETA: <b>{amb_time}</b>"
        
        folium.Marker(
            location=amb['location'],
            popup=folium.Popup(popup_text, max_width=250),
            icon=folium.Icon(color=icon_color, icon='ambulance', prefix='fa')
        ).add_to(m)

    for hospital in hospitals:
        icon_color = 'purple' if hospital['name'] == closest_hosp['name'] else 'darkpurple'
        popup_text = hospital['name']
        if hospital['name'] == closest_hosp['name']:
            popup_text = f"🏥 <b>{hospital['name']}</b><br>📏 Distance: <b>{hosp_dist}</b><br>⏱ ETA: <b>{hosp_time}</b>"

        folium.Marker(
            location=hospital['location'],
            popup=folium.Popup(popup_text, max_width=250),
            icon=folium.Icon(color=icon_color, icon='plus', prefix='fa')
        ).add_to(m)

    draw_google_route_on_map(amb_route, m, color='blue')
    draw_google_route_on_map(hosp_route, m, color='purple')

    m.save("static/ambulance_dispatch_map.html")
    print("✅ Map saved as ambulance_dispatch_map.html")
    print(f"🟢 Closest Ambulance: {closest_amb['name']}")
    print(f"   📏 Distance: {amb_dist}, ⏱ ETA: {amb_time}")
    print(f"🏥 Closest Hospital: {closest_hosp['name']}")
    print(f"   📏 Distance: {hosp_dist}, ⏱ ETA: {hosp_time}")
    
    return {
        "ambulance_username": closest_amb['username'],
        "patient_location": patient_location,
        "ambulance_name": closest_amb['name'],
        "hospital_name": closest_hosp['name'],
        "eta_to_patient": amb_time,
        "eta_to_hospital": hosp_time
    }