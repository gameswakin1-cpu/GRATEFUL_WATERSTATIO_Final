// Leaflet.js CDN and basic map logic for Django template integration
// This file can be included in the order detail template to render a map

document.addEventListener('DOMContentLoaded', function() {
    const mapDiv = document.getElementById('order-map');
    if (!mapDiv) return;
    const address = mapDiv.getAttribute('data-address');
    if (!address) return;

    // Use Nominatim for geocoding (OpenStreetMap)
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`)
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                const lat = parseFloat(data[0].lat);
                const lon = parseFloat(data[0].lon);
                const map = L.map('order-map').setView([lat, lon], 16);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                    attribution: '© OpenStreetMap contributors'
                }).addTo(map);
                L.marker([lat, lon]).addTo(map)
                    .bindPopup('Delivery Location').openPopup();
            } else {
                mapDiv.innerHTML = '<p>Location not found.</p>';
            }
        })
        .catch(() => {
            mapDiv.innerHTML = '<p>Map could not be loaded.</p>';
        });
});
