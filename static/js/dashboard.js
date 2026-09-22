document.addEventListener('DOMContentLoaded', () => {
    const API_BASE = '/api';

    // State
    let currentLocation = 'Hyderabad';
    let trendChart, featureChart, metricsChart, map;
    let suitabilityLayer = null;

    // Elements
    const locSelect = document.getElementById('location-select');
    const navItems = document.querySelectorAll('.list-group-item');
    const sections = document.querySelectorAll('.content-section');

    // Initialize
    async function init() {
        await loadLocations();
        setupNavigation();
        setupMap();
        updateDashboard();
    }

    async function loadLocations() {
        try {
            const res = await fetch(`${API_BASE}/locations`);
            const locations = await res.json();
            locSelect.innerHTML = locations.map(loc =>
                `<option value="${loc}" ${loc === currentLocation ? 'selected' : ''}>${loc}</option>`
            ).join('');

            locSelect.addEventListener('change', (e) => {
                currentLocation = e.target.value;
                updateDashboard();
            });
        } catch (e) { console.error("Error loading locations", e); }
    }

    function setupNavigation() {
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const target = item.id.replace('nav-', 'content-');

                // Update active class
                navItems.forEach(i => i.classList.remove('active'));
                item.classList.add('active');

                // Switch sections
                sections.forEach(s => s.classList.add('d-none'));
                document.getElementById(target).classList.remove('d-none');

                // Update Title
                document.getElementById('page-title').innerText = item.innerText.trim();

                if(target === 'content-gis') {
                    setTimeout(() => map.invalidateSize(), 200);
                }
            });
        });
    }

    function setupMap() {
        map = L.map('gis-map').setView([17.3850, 78.4867], 11);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);
    }

    async function updateDashboard() {
        // 1. Update KPIs & Prediction
        try {
            const res = await fetch(`${API_BASE}/prediction/${currentLocation}`);
            const data = await res.json();

            document.getElementById('kpi-availability').innerText = `${data.predicted_availability}%`;
            document.getElementById('avail-progress').style.width = `${data.predicted_availability}%`;
            document.getElementById('kpi-risk').innerText = data.risk_level;

            const riskBadge = document.getElementById('risk-badge');
            riskBadge.innerText = data.risk_level;
            riskBadge.className = `badge badge-risk-${data.risk_level.toLowerCase()}`;

            // Mock values for GW and Res based on location for demo
            document.getElementById('kpi-gw').innerText = `${(Math.random()*20 + 10).toFixed(1)} m`;
            document.getElementById('kpi-res').innerText = `${(Math.random()*40 + 30).toFixed(1)}%`;
        } catch (e) { console.error("KPI update error", e); }

        // 2. Update Trend Chart
        updateTrendChart();

        // 3. Update Feature Chart
        updateFeatureChart();
    }

    async function updateTrendChart() {
        try {
            const res = await fetch(`${API_BASE}/water-data/${currentLocation}`);
            const data = await res.json();

            const labels = data.map(d => d.date.split('T')[0]).reverse();
            const values = data.map(d => d.availability).reverse();

            if(trendChart) trendChart.destroy();

            const ctx = document.getElementById('trendChart').getContext('2d');
            trendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Water Availability Index (%)',
                        data: values,
                        borderColor: '#0dcaf0',
                        backgroundColor: 'rgba(13, 202, 240, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, max: 100 } }
                }
            });
        } catch (e) { console.error("Trend chart error", e); }
    }

    function updateFeatureChart() {
        // Static features for demo as per ML model
        const features = ['Groundwater', 'Reservoir', 'Rainfall', 'Temperature', 'Population'];
        const importance = [0.45, 0.30, 0.15, 0.05, 0.05];

        if(featureChart) featureChart.destroy();

        const ctx = document.getElementById('featureChart').getContext('2d');
        featureChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: features,
                datasets: [{
                    label: 'Importance',
                    data: importance,
                    backgroundColor: '#0dcaf0'
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true, max: 1 } }
            }
        });
    }

    // GIS Layer Logic
    window.updateMapLayer = async function(type) {
        if(suitabilityLayer) map.removeLayer(suitabilityLayer);

        try {
            const res = await fetch(`${API_BASE}/gis/suitability`);
            const sites = await res.json();

            suitabilityLayer = L.layerGroup();
            sites.forEach(site => {
                const color = site.score > 70 ? 'green' : site.score > 40 ? 'orange' : 'red';
                L.circleMarker([site.lat, site.lon], {
                    radius: 8,
                    fillColor: color,
                    color: '#fff',
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                }).bindPopup(`
                    <strong>Suitability: ${site.class}</strong><br>
                    Score: ${site.score}%
                `).addTo(suitabilityLayer);
            });

            suitabilityLayer.addTo(map);
        } catch (e) { console.error("GIS map error", e); }
    };

    init();
});
