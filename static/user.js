// Live location tracking for patient (user portal)
// Uses browser Geolocation API and Leaflet for map display

let map, marker;

function initLiveMap() {
    if (!document.getElementById('map')) return;
    map = L.map('map').setView([20.5937, 78.9629], 5); // Default: India center
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }).addTo(map);
}

function updateLocationOnMap(lat, lng) {
    if (!map) return;
    if (!marker) {
        marker = L.marker([lat,lng ]).addTo(map);
    } else {
        marker.setLatLng([lat, lng]);
    }
    map.setView([lat, lng], 15);
}

function startLiveLocationTracking() {
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser');
        return;
    }
    navigator.geolocation.watchPosition(
        (position) => {
            const { latitude, longitude } = position.coords;
            document.getElementById('latitude').value = latitude;
            document.getElementById('longitude').value = longitude;
            updateLocationOnMap(latitude, longitude);
        },
        (error) => {
            alert('Unable to retrieve your location: ' + error.message);
        },
        { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
    );
}

document.addEventListener('DOMContentLoaded', () => {
    initLiveMap();
    // Disable the submit button by default
    const bookButton = document.getElementById('bookButton');
    if (bookButton) bookButton.disabled = true;
    let locationSet = false;

    function enableButtonIfReady() {
        const lat = document.getElementById('latitude').value;
        const lon = document.getElementById('longitude').value;
        if (lat && lon && !isNaN(lat) && !isNaN(lon)) {
            locationSet = true;
            if (bookButton) bookButton.disabled = false;
            document.getElementById('status-text').innerText = 'Live location acquired. You can now book an ambulance.';
        }
    }

    // Patch startLiveLocationTracking to enable button when ready
    function patchedStartLiveLocationTracking() {
        if (!navigator.geolocation) {
            alert('Geolocation is not supported by your browser');
            return;
        }
        navigator.geolocation.watchPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                document.getElementById('latitude').value = latitude;
                document.getElementById('longitude').value = longitude;
                updateLocationOnMap(latitude, longitude);
                enableButtonIfReady();
            },
            (error) => {
                document.getElementById('status-text').innerText = 'Unable to retrieve your location. Please enable location services and reload the page.';
                if (bookButton) bookButton.disabled = true;
            },
            { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
        );
    }

    patchedStartLiveLocationTracking();

    // Prevent form submission if location is not set
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            if (!locationSet) {
                e.preventDefault();
                document.getElementById('status-text').innerText = 'Waiting for your live location. Please allow location access.';
            }
        });
    }
});
