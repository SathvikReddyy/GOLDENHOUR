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

    document.getElementById('status-text').innerText = `Urgency selected: ${level}. Waiting for live location...`;
    checkIfReady();
}

// Enable booking button only if location & urgency are set
function checkIfReady() {
    const bookButton = document.getElementById('bookButton');
    if (!bookButton) return;

    if (locationSet && urgencySet) {
        bookButton.disabled = false;
        document.getElementById('status-text').innerText = `✅ Ready! You can now book an ambulance.`;
    } else {
        bookButton.disabled = true;
    }
}

// Confirm booking: ensure ambulance type is selected
function confirmBooking() {
    const selectedType = document.querySelector('input[name="ambTypeOptions"]:checked');
    if (!selectedType) {
        alert("Please select an ambulance type.");
        return;
    }
    document.getElementById('ambulance_type').value = selectedType.value;
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
            document.getElementById('status-text').innerText = 'Unable to retrieve your location.';
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
