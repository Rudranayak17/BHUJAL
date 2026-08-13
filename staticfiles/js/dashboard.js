document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. CONFIG & DATA ---
    const STORAGE_KEY = 'hydro_bookmarks';
    // Ideally, fetch this from an API endpoint, but hardcoded for now as per your request
    const dataMap = {
        "Andhra Pradesh": ["Anantapur","Chittoor","East Godavari","Guntur","Kadapa","Krishna","Kurnool","Prakasam","Srikakulam","Visakhapatnam","Vizianagaram","West Godavari"],
        "Madhya Pradesh": ["Agar Malwa","Alirajpur",
    "Anuppur",
    "Ashoknagar",
    "Balaghat",
    "Barwani",
    "Betul",
    "Bhind",
    "Bhopal",
    "Burhanpur",
    "Chhatarpur",
    "Chhindwara",
    "Damoh",
    "Datia",
    "Dewas",
    "Dhar",
    "Dindori",   
    "Guna",
    "Gwalior",
    "Harda",
    "Hoshangabad",
    "Indore",
    "Jabalpur",
    "Jhabua",
    "Katni",
    "Khandwa",
    "Khargone",
    "Mandla",
    "Mandsaur",
    "Morena",
    "Narsinghpur",
    "Neemuch",
    "Panna",
    "Raisen",
    "Rajgarh",
    "Ratlam",
    "Rewa",
    "Sagar",
    "Satna",
    "Sehore",
    "Seoni",
    "Shahdol",
    "Shajapur",
    "Sheopur",
    "Shivpuri",
    "Sidhi",
    "Singrauli",
    "Tikamgarh",
    "Ujjain",
    "Umaria",
    "Vidisha"], // Add your full list here
        // ... rest of your states
    };

    const stateSelect = document.getElementById('stateSelect');
    const districtSelect = document.getElementById('districtSelect');

    // --- 2. DROPDOWN LOGIC ---
    if (stateSelect && districtSelect) {
        // Populate States
        for (const state in dataMap) {
            const option = document.createElement('option');
            option.value = state;
            option.textContent = state;
            stateSelect.appendChild(option);
        }

        // Handle Change
        stateSelect.addEventListener('change', function() {
            updateDistricts(this.value);
        });

        // Pre-fill from Django Context
        if (window.djangoData.initialState) {
            stateSelect.value = window.djangoData.initialState;
            updateDistricts(window.djangoData.initialState);
            if (window.djangoData.initialDistrict) {
                districtSelect.value = window.djangoData.initialDistrict;
            }
        }
    }

    function updateDistricts(selectedState) {
        districtSelect.innerHTML = '<option value="">-- Select District --</option>';
        if (selectedState && dataMap[selectedState]) {
            dataMap[selectedState].forEach(district => {
                const option = document.createElement('option');
                option.value = district;
                option.textContent = district;
                districtSelect.appendChild(option);
            });
        }
    }

    // --- 3. BOOKMARK LOGIC ---
    const list = document.getElementById('bookmarksList');
    const noMsg = document.getElementById('noBookmarksMsg');
    const btnSave = document.getElementById('btnSaveLocation');
    const btnLogout = document.getElementById('logoutBtn');

    if (btnLogout) {
        btnLogout.addEventListener('click', () => localStorage.removeItem(STORAGE_KEY));
    }

    // Auto-fill function (attached to window to be accessible from HTML onclicks generated in JS)
    window.autoFill = function(state, district) {
        stateSelect.value = state;
        updateDistricts(state);
        districtSelect.value = district;
    };

    window.deleteBookmark = function(event, id) {
        event.stopPropagation();
        if(!confirm("Remove this location?")) return;
        let saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
        saved = saved.filter(item => item.id !== id);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
        renderBookmarks();
    };

    function renderBookmarks() {
        const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
        list.innerHTML = '';
        
        if (saved.length === 0) {
            noMsg.style.display = 'block';
        } else {
            noMsg.style.display = 'none';
            saved.forEach(loc => {
                const card = `
                <div class="bookmark-card" onclick="autoFill('${loc.state}', '${loc.district}')">
                    <div class="bookmark-info">
                        <span class="material-symbols-outlined bookmark-icon">location_on</span>
                        <div>
                            <div style="font-weight:600;">${loc.district}</div>
                            <div style="font-size:0.8em; color:var(--text-muted);">${loc.state}</div>
                        </div>
                    </div>
                    <div class="delete-btn" onclick="deleteBookmark(event, ${loc.id})">
                        <span class="material-symbols-outlined" style="font-size:1.2rem;">close</span>
                    </div>
                </div>`;
                list.insertAdjacentHTML('beforeend', card);
            });
        }
    }

    if (btnSave) {
        btnSave.addEventListener('click', function() {
            const state = stateSelect.value;
            const district = districtSelect.value;
            if(!state || !district) { alert("Please select a State and District first."); return; }

            const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
            if (saved.some(item => item.state === state && item.district === district)) {
                alert("Location already saved.");
                return;
            }

            saved.unshift({ id: Date.now(), state, district });
            localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
            renderBookmarks();
        });
    }

    // Initial Render
    renderBookmarks();

    // --- 4. PLOTLY LOGIC ---
    if (window.djangoData.plotJson) {
        const plotData = window.djangoData.plotJson;
        
        // Layout Styling
        if(!plotData.layout) plotData.layout = {};
        plotData.layout.paper_bgcolor = 'rgba(0,0,0,0)';
        plotData.layout.plot_bgcolor = 'rgba(0,0,0,0)';
        plotData.layout.font = { family: 'Inter, sans-serif', color: '#94a3b8' };
        
        const axisConfig = { gridcolor: '#2d333b', zerolinecolor: '#3b82f6', linecolor: '#94a3b8' };
        plotData.layout.xaxis = Object.assign(plotData.layout.xaxis || {}, axisConfig);
        plotData.layout.yaxis = Object.assign(plotData.layout.yaxis || {}, axisConfig);
        plotData.layout.margin = { l: 40, r: 20, t: 20, b: 40 };

        Plotly.newPlot('myDiv', plotData.data, plotData.layout, { responsive: true, displayModeBar: false });

        // Custom Legend Controls
        const controlsDiv = document.getElementById('station-controls');
        if(controlsDiv && plotData.data) {
            plotData.data.forEach((trace, index) => {
                const label = document.createElement('label');
                label.className = 'station-chip active';
                
                const cb = document.createElement('input');
                cb.type = 'checkbox';
                cb.checked = true;
                
                cb.addEventListener('change', function(){
                    const update = {'visible': this.checked ? true : 'legendonly'};
                    Plotly.restyle('myDiv', update, [index]);
                    this.checked ? label.classList.add('active') : label.classList.remove('active');
                });

                label.append(cb, Object.assign(document.createElement('div'), {className: 'dot'}), document.createTextNode(trace.name || `Trace ${index}`));
                controlsDiv.appendChild(label);
            });
        }
    }
});