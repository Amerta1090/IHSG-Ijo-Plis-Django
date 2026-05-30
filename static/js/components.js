function initComponents(historicalData, predictionData) {
    initConfidenceGauge();
    initExportButton();
    initRefreshButton();
}

function initConfidenceGauge() {
    var arc = document.getElementById('confidence-arc');
    var text = document.getElementById('confidence-text');
    if (!arc || !text) return;

    var score = parseInt(text.textContent) || 0;
    var circumference = 2 * Math.PI * 42;
    var offset = circumference - (score / 100) * circumference;

    // Color based on score
    var color = '#ef4444';
    if (score >= 70) color = '#22c55e';
    else if (score >= 40) color = '#f59e0b';

    arc.style.stroke = color;

    setTimeout(function () {
        arc.style.strokeDashoffset = offset;
    }, 300);
}

function initExportButton() {
    var btn = document.getElementById('export-btn');
    if (!btn) return;

    btn.addEventListener('click', function () {
        if (!hybridChart) return;

        var link = document.createElement('a');
        link.download = 'ihsg-chart-' + new Date().toISOString().slice(0, 10) + '.png';
        link.href = hybridChart.toBase64Image('image/png', 1);
        link.click();
    });
}

function initRefreshButton() {
    var btn = document.getElementById('refresh-btn');
    if (!btn) return;

    btn.addEventListener('click', function () {
        this.disabled = true;
        var svg = this.querySelector('svg');
        var text = this.querySelector('span');
        if (svg) svg.classList.add('animate-spin');
        if (text) text.textContent = 'Refreshing...';
        window.location.reload();
    });
}
