document.addEventListener('DOMContentLoaded', function() {
    if (!window.plotDataJson) return; // safety check

    var plotData = plotDataJson;

    // --- Theme Adaptation ---
    if(!plotData.layout) plotData.layout = {};
    plotData.layout.paper_bgcolor = 'rgba(0,0,0,0)';
    plotData.layout.plot_bgcolor = 'rgba(0,0,0,0)';
    plotData.layout.font = { family: 'Inter, sans-serif', color: '#94a3b8' };

    // Grid lines to match theme border
    var axisConfig = {
        gridcolor: '#2d333b',
        zerolinecolor: '#3b82f6',
        linecolor: '#94a3b8',
        tickcolor: '#94a3b8'
    };
    plotData.layout.xaxis = Object.assign(plotData.layout.xaxis || {}, axisConfig);
    plotData.layout.yaxis = Object.assign(plotData.layout.yaxis || {}, axisConfig);

    // Remove margins to fit card
    plotData.layout.margin = { l: 40, r: 20, t: 20, b: 40 };
    plotData.layout.autosize = true;

    var config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot('myDiv', plotData.data, plotData.layout, config);

    // --- Create Horizontal "Chips" for Toggles ---
    var controlsDiv = document.getElementById('station-controls');

    plotData.data.forEach(function(trace, index){
        var label = document.createElement('label');
        label.className = 'station-chip active';

        var cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.checked = true;
        cb.id = 'cb'+index;

        var dot = document.createElement('div');
        dot.className = 'dot';

        var span = document.createElement('span');
        span.innerText = trace.name;

        cb.addEventListener('change', function(){
            var update = {'visible': this.checked ? true : 'legendonly'};
            Plotly.restyle('myDiv', update, [index]);

            if(this.checked) label.classList.add('active');
            else label.classList.remove('active');
        });

        label.appendChild(cb);
        label.appendChild(dot);
        label.appendChild(span);
        controlsDiv.appendChild(label);
    });
});
