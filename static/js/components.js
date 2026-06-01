function initComponents(historicalData, predictionData) {
    initConfidenceGauge();
    initExportButton();
    initRefreshButton();
    initFadeInObserver();
    initDecompositionCharts();
}

function initConfidenceGauge() {
    var arc = document.getElementById('confidence-arc');
    var text = document.getElementById('confidence-text');
    if (!arc || !text) return;

    var score = parseInt(text.textContent) || 0;
    var circumference = 2 * Math.PI * 42;
    var offset = circumference - (score / 100) * circumference;

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

        fetch('/api/metrics.json')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                window.location.reload();
            })
            .catch(function () {
                window.location.reload();
            });
    });
}

function initFadeInObserver() {
    if (!window.IntersectionObserver) {
        document.querySelectorAll('.fade-in').forEach(function (el) {
            el.classList.add('visible');
        });
        return;
    }

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.fade-in').forEach(function (el) {
        observer.observe(el);
    });
}

function initDecompositionCharts() {
    var section = document.getElementById('decomposition-section');
    if (!section) return;

    var skeleton = document.getElementById('decomposition-skeleton');
    var charts = document.getElementById('decomposition-charts');
    if (skeleton) skeleton.classList.remove('hidden');

    fetch('/api/decomposition.json')
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (skeleton) skeleton.classList.add('hidden');
            if (charts) charts.classList.remove('hidden');

            var commonOpts = {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1a2338',
                        titleColor: '#f1f5f9',
                        bodyColor: '#94a3b8',
                        borderColor: '#1e293b',
                        borderWidth: 1,
                        padding: 8,
                        cornerRadius: 6,
                        bodyFont: { family: 'JetBrains Mono, monospace', size: 10 },
                    },
                },
                scales: {
                    x: {
                        grid: { color: '#1e293b', drawBorder: false },
                        ticks: { color: '#64748b', font: { size: 8 }, maxTicksLimit: 8, autoSkip: true },
                    },
                    y: {
                        grid: { color: '#1e293b', drawBorder: false },
                        ticks: { color: '#64748b', font: { size: 8 }, callback: function (v) { return v.toFixed(1); } },
                    },
                },
            };

            function buildDecompChart(canvasId, dataArr, color) {
                var canvas = document.getElementById(canvasId);
                if (!canvas || !dataArr || dataArr.length === 0) return;
                var labels = dataArr.map(function (d) { return d.ds; });
                var values = dataArr.map(function (d) { return d.value; });
                new Chart(canvas, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: values,
                            borderColor: color,
                            backgroundColor: color + '20',
                            borderWidth: 1.5,
                            pointRadius: 0,
                            fill: true,
                            tension: 0.3,
                        }],
                    },
                    options: commonOpts,
                });
            }

            buildDecompChart('trendChart', data.trend, '#3b82f6');
            buildDecompChart('weeklyChart', data.weekly, '#22c55e');
            buildDecompChart('yearlyChart', data.yearly, '#f59e0b');
        })
        .catch(function () {
            if (skeleton) skeleton.classList.add('hidden');
            if (charts) {
                charts.innerHTML = '<div class="text-center py-6 text-sm text-[#64748b]">Decomposition data unavailable</div>';
            }
        });
}