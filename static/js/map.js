// 1. Initialize the Map
// Nairobi's coordinates
const map = L.map('map').setView([-1.286389, 36.817223], 12);

// Add the base map layer (OpenStreetMap)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// 2. Define Risk Color Styling
function getRiskColor(risk) {
    switch(risk.toLowerCase()) {
        case 'high': return '#dc3545'; // Red
        case 'medium': return '#fd7e14'; // Orange
        case 'low': return '#28a745'; // Green
        default: return '#6c757d'; // Grey
    }
}

function styleWard(feature) {
    return {
        fillColor: getRiskColor(feature.properties.current_risk_level),
        weight: 2,
        opacity: 1,
        color: 'white',
        fillOpacity: 0.8
    };
}

// 3. Add GeoJSON Layer and Filter Logic
let wardLayer; // Define the layer in a broad scope

fetch('/api/ward-data/')
    .then(response => response.json())
    .then(data => {
        wardLayer = L.geoJSON(data, {
            style: styleWard,
            onEachFeature: function(feature, layer) {
                // Add popups
                layer.bindPopup(
                    `<strong>${feature.properties.name}</strong><br>` +
                    `Risk: ${feature.properties.current_risk_level}`
                );
            }
        }).addTo(map);
    })
    .catch(error => console.error('Error fetching wards:', error));


const riskFilter = document.getElementById('risk-level');

// Add an event listener that fires when the dropdown's value changes
riskFilter.addEventListener('change', function(e) {
    // 'e.target.value' is the selected value (e.g., "High", "Low", "all")
    const selectedRisk = e.target.value;

    if (wardLayer) {
        // Loop through each ward (layer) on the map
        wardLayer.eachLayer(function(layer) {
            const risk = layer.feature.properties.current_risk_level;

            if (selectedRisk === 'all' || risk === selectedRisk) {
                layer.setStyle({
                    opacity: 1,
                    fillOpacity: 0.8,
                    interactive: true
                });
            } else
                 {
                layer.setStyle({
                    opacity: 0,
                    fillOpacity: 0,
                    interactive: false
                });
            }
        });
    }
});