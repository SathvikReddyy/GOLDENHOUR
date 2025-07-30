document.addEventListener('DOMContentLoaded', function () {

    // IMPORTANT: Paste your Google Maps API Key here
    const GMAPS_API_KEY = 'AIzaSyCfGUtxuviXpo2G9kRdyp8-8loCkR8rxsA';

    const map = L.map('map').setView([17.435, 78.47], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    let userMarker; 

    const bookingForm = document.getElementById('bookingForm');
    const bookButton = document.getElementById('bookButton');
    const statusText = document.getElementById('status-text');
    const latInput = document.getElementById('latitude');
    const lngInput = document.getElementById('longitude');

    bookingForm.addEventListener('submit', function (event) {
        event.preventDefault(); 
        
        statusText.textContent = 'Finding your location... This may take a moment.';
        bookButton.disabled = true;
        bookButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Finding Location...';

        // --- NEW: Using Google Geolocation API with fetch ---
        fetch(`https://www.googleapis.com/geolocation/v1/geolocate?key=${GMAPS_API_KEY}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({}) // Body can be empty for a basic lookup
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Call the success function with the retrieved location data
            success(data.location, data.accuracy);
        })
        .catch(error => {
            // Call the error function
            handleError(error);
        });
    });

    // Modified success function
    function success(location, accuracy) {
        const latitude = location.lat;
        const longitude = location.lng;

        statusText.textContent = `Location found with an accuracy of ${Math.round(accuracy)} meters. Dispatching...`;

        map.setView([latitude, longitude], 15);
        if (userMarker) {
            map.removeLayer(userMarker);
        }
        userMarker = L.marker([latitude, longitude]).addTo(map)
            .bindPopup(`<b>Your Estimated Location</b><br>Accuracy: ${Math.round(accuracy)}m`)
            .openPopup();
        
        latInput.value = latitude;
        lngInput.value = longitude;
        
        bookingForm.submit();
    }

    // Renamed error function
    function handleError(error) {
        console.error("Geolocation API Error:", error);
        statusText.textContent = 'Could not determine your location. Please try again.';
        bookButton.disabled = false;
        bookButton.innerHTML = '<i class="fas fa-ambulance me-2"></i>Book Nearest Ambulance';
    }
});