let map, marker;
let locationSet = false;
let urgencySet = false;

// Initialize Leaflet map
function initLiveMap() {
    const mapDiv = document.getElementById('map');
    if (!mapDiv) return;
    map = L.map('map').setView([20.5937, 78.9629], 5); // Default view: India
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19, attribution: '© OpenStreetMap'
    }).addTo(map);
}

function loadAmbulancesAndHospitals(ambulances, hospitals) {
    if (!map) return;

    // Show hospitals
    hospitals.forEach(hospital => {
        L.marker(hospital.location, {
            icon: L.icon({
                iconUrl: "https://cdn-icons-png.flaticon.com/512/684/684908.png",
                iconSize: [30, 30]
            })
        }).addTo(map).bindPopup(`🏥 ${hospital.name}`);
    });

    // Show ambulances
    ambulances.forEach(amb => {
        let color = (amb.type && amb.type.toLowerCase() === "government") ? "blue" : "green";
        L.marker(amb.location, {
            icon: L.divIcon({
                className: "custom-marker",
                html: `<i class="fa-solid fa-ambulance" style="color:${color}; font-size:20px;"></i>`
            })
        }).addTo(map).bindPopup(`🚑 ${amb.name} (${amb.type || 'unknown'})`);
    });
}

// Update marker position on the map
function updateLocationOnMap(lat, lng) {
    if (!map) return;
    if (!marker) marker = L.marker([lat, lng]).addTo(map);
    else marker.setLatLng([lat, lng]);
    map.setView([lat, lng], 15);
}

// Set urgency level when a triage button is clicked
function setUrgency(level) {
    document.getElementById('urgency').value = level;
    urgencySet = true;

    document.querySelectorAll('.triage-buttons .btn').forEach(btn => btn.classList.remove('active'));
    const selectedBtn = Array.from(document.querySelectorAll('.triage-buttons .btn'))
        .find(btn => btn.innerText.includes(level));
    if (selectedBtn) selectedBtn.classList.add('active');

    if (document.getElementById('status-text')) {
        document.getElementById('status-text').innerText = `Urgency selected: ${level}. Waiting for live location...`;
    }
    checkIfReady();
}

// Enable booking button only if location & urgency are set
function checkIfReady() {
    const bookButton = document.getElementById('bookButton');
    if (!bookButton) return;

    if (locationSet && urgencySet) {
        bookButton.disabled = false;
        if (document.getElementById('status-text')) document.getElementById('status-text').innerText = `✅ Ready! You can now book an ambulance.`;
    } else {
        bookButton.disabled = true;
    }
}

function confirmBooking() {
    const selectedType = document.querySelector('input[name="ambTypeOptions"]:checked');
    if (!selectedType) {
        alert("Please select an ambulance type.");
        return;
    }

    // normalise to lower-case values expected by server/simulation
    document.getElementById('ambulance_type').value = selectedType.value.toLowerCase();

    // Close the modal before submitting
    const modalEl = document.getElementById('ambulanceTypeModal');
    const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    modal.hide();

    // Submit the booking form
    document.getElementById('bookingForm').submit();
}

// Track user's live location using browser geolocation
function startLiveLocationTracking() {
    if (!navigator.geolocation) {
        alert('Geolocation not supported');
        return;
    }

    navigator.geolocation.watchPosition(
        (position) => {
            const { latitude, longitude } = position.coords;
            document.getElementById('latitude').value = latitude;
            document.getElementById('longitude').value = longitude;
            updateLocationOnMap(latitude, longitude);
            locationSet = true;
            checkIfReady();
        },
        () => {
            if (document.getElementById('status-text')) document.getElementById('status-text').innerText = 'Unable to retrieve your location.';
            locationSet = false;
            checkIfReady();
        },
        { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
    );
}

document.addEventListener('DOMContentLoaded', () => {
    initLiveMap();
    startLiveLocationTracking();
    if (document.getElementById('bookButton')) document.getElementById('bookButton').disabled = true;
});
