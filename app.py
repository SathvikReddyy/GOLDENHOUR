from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from simulation import run_simulation_gmaps, GMAPS_API_KEY
import os

from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv('MAPS_API_KEY')

app = Flask(__name__)
app.secret_key = SECRET_KEY

# --- CREDENTIALS ---
ADMIN_CREDENTIALS = {'username': 'admin', 'password': 'admin123'}
DRIVER_CREDENTIALS = {
    "secunderabad_driver": "sec123", "nampally_driver": "namp123",
    "banjara_driver": "ban123", "ameerpet_driver": "ame123",
    "hitec_driver": "hitec123", "gachibowli_driver": "gachi123",
    "kukatpally_driver": "kphb123", "madhapur_driver": "madha123"
}
USER_CREDENTIALS = {
    "Sathvik_Reddy": "sathvik123", "Rakshith_Raj": "rakshith123",
    "Mani_Kanta": "mani123", "Abhinav_Sharma": "abhinav123"
}
USER_DETAILS = {
    "Sathvik_Reddy": {"name": "Sathvik Reddy", "phone_no": "7989154351"},
    "Rakshith_Raj": {"name": "Rakshith", "phone_no": "7093297061"},
    "Mani_Kanta": {"name": "Mani Kanta", "phone_no": "8897521925"},
    "Abhinav_Sharma": {"name": "Abhinav", "phone_no": "8328660108"}
}

# --- Track dispatches & driver status ---
ACTIVE_DISPATCHES = {}  # {driver_username: dispatch_info}
DRIVER_STATUS = {}      # {driver_username: {'on_duty': True/False, 'assigned': True/False}}

# --- HOME ---
@app.route('/')
def home():
    return render_template('index.html')

# --- ADMIN ---
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_CREDENTIALS['username'] and request.form.get('password') == ADMIN_CREDENTIALS['password']:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid Credentials")
    return render_template('admin_login.html')

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    dispatched = None  # Initialize

    if request.method == 'POST':
        lat = float(request.form['latitude'])
        lng = float(request.form['longitude'])
        patient_location = (lat, lng)
        ambulance_type = request.form.get('ambulance_type', 'private')

        # Pass DRIVER_STATUS to simulation
        dispatched = run_simulation_gmaps(patient_location, selected_type=ambulance_type, driver_status=DRIVER_STATUS)


        if dispatched:
            dispatched['patient_name'] = request.form.get('name', 'Unknown')
            dispatched['patient_mobile'] = request.form.get('mobile', 'Unknown')
            dispatched['patient_location'] = patient_location

            # Safe extraction
            dispatched['ambulance_name'] = dispatched['ambulance']['name']
            dispatched['hospital_name'] = dispatched.get('hospital', {}).get('name', 'Unknown Hospital')
            dispatched['eta_to_patient'] = dispatched.get('eta_to_patient', 'N/A')
            dispatched['eta_to_hospital'] = dispatched.get('eta_to_hospital', 'N/A')

            driver_username = dispatched['ambulance']['username']
            ACTIVE_DISPATCHES[driver_username] = dispatched
            DRIVER_STATUS[driver_username] = {'on_duty': True, 'assigned': True}



    # Pass the dispatched info (None if no dispatch yet)
    return render_template('admin_dashboard.html', dispatched=dispatched)


# --- DRIVER LOGIN ---

@app.route('/driver/login', methods=['GET','POST'])
def driver_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in DRIVER_CREDENTIALS and DRIVER_CREDENTIALS[username] == password:
            session['driver'] = username
            DRIVER_STATUS.setdefault(username, {'on_duty': True, 'assigned': False})
            return redirect(url_for('driver_portal'))
        else:
            return render_template('driver_login.html', error="Invalid Credentials")
    return render_template('driver_login.html')
@app.route('/get_dispatch_status')
def get_dispatch_status():
    driver_id = session.get('driver')
    if not driver_id:
        return jsonify({"error": "Not logged in"}), 401

    dispatch = ACTIVE_DISPATCHES.get(driver_id)
    if not dispatch:
        return jsonify({"status": "no_active_dispatch"})

    return jsonify(dispatch)


@app.route('/driver/portal', methods=['GET', 'POST'])
def driver_portal():
    if 'driver' not in session:
        return redirect(url_for('driver_login'))

    driver_id = session['driver']
    status = DRIVER_STATUS.get(driver_id, {'on_duty': True, 'assigned': False, 'available': True})
    status['available'] = status['on_duty'] and not status['assigned']
    DRIVER_STATUS[driver_id] = status

    dispatch = ACTIVE_DISPATCHES.get(driver_id)
    return render_template('driver_map.html', dispatch=dispatch, status=status)


# --- DRIVER ACTIONS ---
@app.route('/driver/toggle', methods=['POST'])
def driver_toggle():
    driver_id = session.get('driver')
    if not driver_id:
        return jsonify({"error":"Not logged in"}), 401

    data = request.get_json()
    on_duty = data.get('on_duty', True)

    status = DRIVER_STATUS.get(driver_id, {'on_duty': True, 'assigned': False, 'available': True})
    status['on_duty'] = on_duty
    status['available'] = status['on_duty'] and not status['assigned']
    DRIVER_STATUS[driver_id] = status

    return jsonify({"on_duty": on_duty, "available": status['available']})


@app.route('/driver/accept', methods=['POST'])
def driver_accept():
    driver_id = session.get('driver')
    if not driver_id or driver_id not in ACTIVE_DISPATCHES:
        return jsonify({"status": "error", "message": "No active dispatch"}), 400

    dispatch = ACTIVE_DISPATCHES[driver_id]
    dispatch['status'] = 'accepted'  # <-- top-level status for patient polling
    dispatch['ambulance']['status'] = 'accepted'
    DRIVER_STATUS[driver_id]['assigned'] = True
    DRIVER_STATUS[driver_id]['available'] = False

    return jsonify({"status": "success", "message": "Ride accepted"})


@app.route('/driver/deny', methods=['POST'])
def driver_deny():    # match JS function name
    driver_id = session.get('driver')
    if not driver_id or driver_id not in ACTIVE_DISPATCHES:
        return jsonify({"status": "error", "message": "No active dispatch"}), 400

    ACTIVE_DISPATCHES.pop(driver_id)
    DRIVER_STATUS[driver_id]['assigned'] = False
    DRIVER_STATUS[driver_id]['available'] = True

    return jsonify({"status": "success", "message": "Ride denied"})
@app.route('/driver/complete', methods=['POST'])
def driver_complete():
    driver_id = session.get('driver')
    if driver_id and driver_id in ACTIVE_DISPATCHES:
        ACTIVE_DISPATCHES.pop(driver_id)
        DRIVER_STATUS[driver_id]['assigned'] = False
        DRIVER_STATUS[driver_id]['available'] = DRIVER_STATUS[driver_id]['on_duty']
        return jsonify({"status":"completed"})
    return jsonify({"error":"No ride assigned"}), 400

# --- USER LOGIN ---
@app.route('/user/login', methods=['GET','POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            session['user'] = username
            session.pop('dispatch_info', None)
            return redirect(url_for('user_portal'))
        else:
            return render_template('user_login.html', error="Invalid Credentials")
    return render_template('user_login.html')

# --- USER PORTAL ---
@app.route('/user/portal', methods=['GET','POST'])
def user_portal():
    if 'user' not in session:
        return redirect(url_for('user_login'))

    username = session['user']
    user_data = USER_DETAILS.get(username)

    # define fleets/hospitals here (same as simulation)
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

    if request.method == 'POST':
        try:
            lat = float(request.form.get('latitude', 0))
            lon = float(request.form.get('longitude', 0))
        except ValueError:
            return "Invalid coordinates", 400

        ambulance_type = request.form.get('ambulance_type', 'private').lower()

        # run simulation and pass current driver statuses (so simulation only picks available drivers)
        dispatched = run_simulation_gmaps((lat, lon), selected_type=ambulance_type, driver_status=DRIVER_STATUS)

        # if simulation returned a valid ambulance assignment, keep it in session & ACTIVE_DISPATCHES
        if dispatched:
            dispatched['patient_name'] = user_data['name']
            dispatched['patient_mobile'] = user_data['phone_no']
            dispatched['patient_location'] = (lat, lon)

            # Add these 👇 so template conditions work
            dispatched['ambulance_name'] = dispatched['ambulance']['name']
            dispatched['ambulance_type'] = dispatched['ambulance'].get('type', 'unknown')

            dispatched['hospital_name'] = dispatched.get('hospital', {}).get('name', 'Unknown Hospital')

            driver_username = dispatched['ambulance']['username']
            ACTIVE_DISPATCHES[driver_username] = dispatched
            DRIVER_STATUS[driver_username] = {'on_duty': True, 'assigned': True}
            session['dispatch_info'] = dispatched
        else:
            # no ambulance available — clear dispatch_info
            session.pop('dispatch_info', None)


    return render_template(
        'user_portal.html',
        dispatched=session.get('dispatch_info'),
        user=user_data,
        govt_ambulances=govt_fleet,
        private_ambulances=private_fleet,
        hospitals=hospitals,
    )

@app.route("/check_status")
def check_status():
    dispatch_info = session.get("dispatch_info")
    if not dispatch_info:
        return {"status": "no_request"}

    driver_username = dispatch_info["ambulance"]["username"]
    latest_dispatch = ACTIVE_DISPATCHES.get(driver_username)

    if latest_dispatch and latest_dispatch.get("status") == "accepted":
        return {
            "status": "accepted",
            "driver_name": latest_dispatch["ambulance"]["name"],
            "driver_username": driver_username,
            "ambulance_type": latest_dispatch["ambulance"].get("type", "unknown"),
            "hospital_name": latest_dispatch.get("hospital", {}).get("name", "Unknown"),
            "eta_to_patient": latest_dispatch.get("eta_to_patient", "N/A"),
            "eta_to_hospital": latest_dispatch.get("eta_to_hospital", "N/A"),
            "map_url": latest_dispatch.get("map_url")
        }
    return {"status": "waiting"}

# --- LOGOUT ---
@app.route('/logout')
def logout():
    driver_id = session.get('driver')
    if driver_id:
        ACTIVE_DISPATCHES.pop(driver_id, None)
        DRIVER_STATUS[driver_id]['assigned'] = False
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
