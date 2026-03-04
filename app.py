#APP.PY
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from simulation import run_simulation_gmaps, GMAPS_API_KEY
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("MAPS_API_KEY")

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ---------------- CREDENTIALS ----------------
ADMIN_CREDENTIALS = {'username': 'admin', 'password': 'admin123'}

DRIVER_CREDENTIALS = {
    "secunderabad_driver": "sec123",
    "nampally_driver": "namp123",
    "banjara_driver": "ban123",
    "ameerpet_driver": "ame123",
    "hitec_driver": "hitec123",
    "gachibowli_driver": "gachi123",
    "kukatpally_driver": "kphb123",
    "madhapur_driver": "madha123"
}

USER_CREDENTIALS = {
    "Sathvik_Reddy": "sathvik123",
    "Rakshith_Raj": "rakshith123",
    "Mani_Kanta": "mani123",
    "Abhinav_Sharma": "abhinav123"
}

USER_DETAILS = {
    "Sathvik_Reddy": {"name": "Sathvik Reddy", "phone_no": "7989154351"},
    "Rakshith_Raj": {"name": "Rakshith", "phone_no": "7093297061"},
    "Mani_Kanta": {"name": "Mani Kanta", "phone_no": "8897521925"},
    "Abhinav_Sharma": {"name": "Abhinav", "phone_no": "8328660108"}
}


# ---------------- GLOBAL STATE ----------------
ACTIVE_DISPATCHES = {}
DRIVER_STATUS = {}


# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')


# ---------------- ADMIN ----------------
@app.route('/admin/login', methods=['GET', 'POST'])
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

    dispatched = None

    if request.method == 'POST':
        lat = float(request.form['latitude'])
        lng = float(request.form['longitude'])
        ambulance_type = request.form.get('ambulance_type', 'private')

        result = run_simulation_gmaps((lat, lng), selected_type=ambulance_type, driver_status=DRIVER_STATUS)

        # SAFE HANDLING
        if result and result.get("ambulance"):
            dispatched = result

            dispatched['patient_name'] = request.form.get('name', 'Unknown')
            dispatched['patient_mobile'] = request.form.get('mobile', 'Unknown')
            dispatched['patient_location'] = (lat, lng)

            ambulance = dispatched.get("ambulance")
            hospital = dispatched.get("hospital", {})

            dispatched['ambulance_name'] = ambulance.get("name")
            dispatched['hospital_name'] = hospital.get("name", "Unknown Hospital")

            driver_username = ambulance.get("username")
            ACTIVE_DISPATCHES[driver_username] = dispatched
            DRIVER_STATUS[driver_username] = {'on_duty': True, 'assigned': True}

    return render_template('admin_dashboard.html', dispatched=dispatched)


# ---------------- DRIVER ----------------
@app.route('/driver/login', methods=['GET', 'POST'])
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


@app.route('/driver/portal')
def driver_portal():
    if 'driver' not in session:
        return redirect(url_for('driver_login'))

    driver_id = session['driver']
    status = DRIVER_STATUS.get(driver_id, {'on_duty': True, 'assigned': False})
    status['available'] = status['on_duty'] and not status['assigned']
    DRIVER_STATUS[driver_id] = status

    dispatch = ACTIVE_DISPATCHES.get(driver_id)
    return render_template('driver_map.html', dispatch=dispatch, status=status)


@app.route('/driver/accept', methods=['POST'])
def driver_accept():
    driver_id = session.get('driver')
    if driver_id not in ACTIVE_DISPATCHES:
        return jsonify({"error": "No dispatch"}), 400

    dispatch = ACTIVE_DISPATCHES[driver_id]
    dispatch['status'] = 'accepted'
    dispatch['ambulance']['status'] = 'accepted'
    DRIVER_STATUS[driver_id]['assigned'] = True

    return jsonify({"status": "accepted"})


@app.route('/driver/complete', methods=['POST'])
def driver_complete():
    driver_id = session.get('driver')
    if driver_id in ACTIVE_DISPATCHES:
        ACTIVE_DISPATCHES.pop(driver_id)
        DRIVER_STATUS[driver_id]['assigned'] = False
        return jsonify({"status": "completed"})
    return jsonify({"error": "No ride"}), 400


# ---------------- USER ----------------
@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            session['user'] = username
            session.pop("dispatch_info", None)
            return redirect(url_for('user_portal'))

        return render_template('user_login.html', error="Invalid Credentials")

    return render_template('user_login.html')


@app.route('/user/portal', methods=['GET', 'POST'])
def user_portal():
    if 'user' not in session:
        return redirect(url_for('user_login'))

    username = session['user']
    user_data = USER_DETAILS.get(username)

    if request.method == 'POST':
        lat = float(request.form.get('latitude', 0))
        lon = float(request.form.get('longitude', 0))
        ambulance_type = request.form.get('ambulance_type', 'private')

        # ---------------- ADDITION: LOCATION DEBUG + LOCK ----------------
        print("📍 BOOKING LOCATION RECEIVED:", lat, lon)

# If frontend accidentally sends 0,0 → block booking
        if lat == 0 or lon == 0:
           print("⚠️ WARNING: GPS NOT CAPTURED — BLOCKING BOOKING")
           session['dispatch_info'] = {"status": "location_error"}
           return render_template(
               'user_portal.html',
                dispatched=session.get("dispatch_info"),
                user=user_data
      )
# ---------------------------------------------------------------


        result = run_simulation_gmaps((lat, lon), selected_type=ambulance_type, driver_status=DRIVER_STATUS)

        # SAFE HANDLING
        if result and result.get("ambulance"):
            dispatched = result

            ambulance = dispatched.get("ambulance")
            hospital = dispatched.get("hospital", {})

            dispatched['patient_name'] = user_data['name']
            dispatched['patient_mobile'] = user_data['phone_no']
            dispatched['patient_location'] = (lat, lon)

            # ---------------- ADDITION: HARD SAVE LOCATION ----------------
            session['last_patient_location'] = (lat, lon)
            print("📍 LOCATION STORED IN SESSION:", session['last_patient_location'])
# --------------------------------------------------------------


            dispatched['ambulance_name'] = ambulance.get("name")
            dispatched['ambulance_type'] = ambulance.get("type")
            dispatched['hospital_name'] = hospital.get("name")

            driver_username = ambulance.get("username")

            ACTIVE_DISPATCHES[driver_username] = dispatched
            DRIVER_STATUS[driver_username] = {'on_duty': True, 'assigned': True}


            session['dispatch_info'] = dispatched

        else:
            session['dispatch_info'] = {"status": "no_ambulance"}
    
    # ---------------- ADDITION: VERIFY STORED LOCATION ----------------
    if session.get("dispatch_info") and session.get("last_patient_location"):
        print("📍 USING STORED LOCATION:", session.get("last_patient_location"))
# ----------------------------------------------------------------



    return render_template(
        'user_portal.html',
        dispatched=session.get("dispatch_info"),
        user=user_data,
        last_location=session.get("last_patient_location")
    )


# ---------------- STATUS CHECK ----------------
@app.route("/check_status")
def check_status():
    dispatch_info = session.get("dispatch_info")

    if not dispatch_info:
        return {"status": "no_request"}

    ambulance = dispatch_info.get("ambulance")
    if not ambulance:
        return {"status": "waiting"}

    driver_username = ambulance.get("username")
    latest_dispatch = ACTIVE_DISPATCHES.get(driver_username)

    if latest_dispatch and latest_dispatch.get("status") == "accepted":
        return {"status": "accepted"}

    return {"status": "waiting"}


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    driver_id = session.get('driver')

    if driver_id:
        ACTIVE_DISPATCHES.pop(driver_id, None)
        if driver_id in DRIVER_STATUS:
            DRIVER_STATUS[driver_id]['assigned'] = False

    session.clear()
    return redirect(url_for('home'))


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)