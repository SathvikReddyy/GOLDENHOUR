# app.py
from flask import Flask, render_template, request, redirect, url_for, session
import time
from simulation import run_simulation_gmaps, GMAPS_API_KEY

# Initialize the Flask Application
app = Flask(__name__)
app.secret_key = 'a_very_secret_key_for_your_portals'

# --- DATA & CREDENTIALS ---
ADMIN_CREDENTIALS = {'username': 'admin', 'password': 'admin123'}
DRIVER_CREDENTIALS = {
    "secunderabad_driver": "sec123", "nampally_driver": "namp123", "banjara_driver": "ban123",
    "ameerpet_driver": "ame123", "hitec_driver": "hitec123", "gachibowli_driver": "gachi123",
    "kukatpally_driver": "kphb123", "madhapur_driver": "madha123", "uppal_driver": "uppal123",
    "lbnagar_driver": "lbn123", "tarnaka_driver": "tar123", "dilsukhnagar_driver": "dilsuk123",
    "kompally_driver": "kom123", "alwal_driver": "alwal123", "bowenpally_driver": "bowen123",
    "jeedimetla_driver": "jeedi123", "charminar_driver": "char123", "shamshabad_driver": "sham123",
    "mehdipatnam_driver": "mehd123", "falaknuma_driver": "fala123", "narsapur_driver": "nar123" 
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

# NEW: Use this dictionary to track active assignments for drivers
# This is shared across all sessions, but is keyed by driver username
ACTIVE_DISPATCHES = {}

# --- MAIN ROUTE ---
@app.route('/')
def home():
    return render_template('index.html')

# --- ADMIN PORTAL ROUTES ---
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

    if request.method == 'POST':
        lat = float(request.form['latitude'])
        lng = float(request.form['longitude'])
        patient_location = (lat, lng)
        
        dispatched = run_simulation_gmaps(patient_location, GMAPS_API_KEY)
        
        if dispatched:
            # Attach patient info to dispatched dict for admin and driver
            dispatched['patient_name'] = request.form.get('name', 'Unknown')
            dispatched['patient_mobile'] = request.form.get('mobile', 'Unknown')
            dispatched['patient_location'] = (lat, lng)

            # Store dispatch in the admin's session
            session['admin_dispatch'] = dispatched
            # Make the dispatch available for the assigned driver
            driver_username = dispatched['ambulance_username']
            ACTIVE_DISPATCHES[driver_username] = dispatched
        
        return render_template(
            'admin_dashboard.html', 
            dispatched=session.get('admin_dispatch')
        )

    return render_template('admin_dashboard.html', dispatched=session.get('admin_dispatch'))

# --- DRIVER PORTAL ROUTES ---
@app.route('/driver/login', methods=['GET', 'POST'])
def driver_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in DRIVER_CREDENTIALS and DRIVER_CREDENTIALS[username] == password:
            session['driver'] = username
            return redirect(url_for('driver_portal'))
        else:
            return render_template('driver_login.html', error="Invalid Credentials")
    return render_template('driver_login.html')

@app.route('/driver/portal')
def driver_portal():
    if 'driver' not in session:
        return redirect(url_for('driver_login'))

    driver_id = session['driver']
    # Check the shared active dispatches for this driver's assignment
    assigned_dispatch = ACTIVE_DISPATCHES.get(driver_id)
    
    if assigned_dispatch:
        return render_template('driver_map.html', map_available=True, dispatch=assigned_dispatch)
    
    return render_template('driver_map.html', map_available=False)

# --- USER PORTAL ROUTES (FIXED) ---
@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            session['user'] = username
            # Clear any old dispatch info when a new user logs in
            session.pop('dispatch_info', None) 
            return redirect(url_for('user_portal'))
        else:
            return render_template('user_login.html', error="Invalid Credentials")
    return render_template('user_login.html')

@app.route('/user/portal', methods=['GET', 'POST'])
def user_portal():
    if 'user' not in session:
        return redirect(url_for('user_login'))

    username = session['user']
    user_data = USER_DETAILS.get(username)

    if request.method == 'POST':
        lat_str = request.form.get('latitude', '').strip()
        lon_str = request.form.get('longitude', '').strip()
        if not lat_str or not lon_str:
            return "Latitude and Longitude are required", 400
        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            return "Invalid latitude or longitude value", 400
        patient_location = (lat, lon)

        dispatched = run_simulation_gmaps(patient_location, GMAPS_API_KEY)

        if dispatched:
            # Add patient info to dispatched dict for driver portal
            dispatched['patient_name'] = user_data['name'] if user_data else 'Unknown'
            dispatched['patient_mobile'] = user_data['phone_no'] if user_data else 'Unknown'
            dispatched['patient_location'] = (lat, lon)

            # Store the dispatch info ONLY in this user's session
            session['dispatch_info'] = dispatched
            # Make the dispatch available for the assigned driver
            driver_username = dispatched['ambulance_username']
            ACTIVE_DISPATCHES[driver_username] = dispatched

    # Get dispatch info from the session, not a global variable
    dispatched_data = session.get('dispatch_info')
    return render_template('user_portal.html', dispatched=dispatched_data, user=user_data)


# --- SHARED LOGOUT ROUTE ---
@app.route('/logout')
def logout():
    # If a driver logs out, remove their completed job from active dispatches
    if 'driver' in session:
        driver_id = session.get('driver')
        ACTIVE_DISPATCHES.pop(driver_id, None)

    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)