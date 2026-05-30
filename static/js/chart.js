let hybridChart = null;

function getDateRange(data, range) {
    if (!data || data.length === 0) return [];
    var now = new Date();
    var cutoff = new Date(0);
    switch (range) {
        case '1M': cutoff = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate()); break;
        case '3M': cutoff = new Date(now.getFullYear(), now.getMonth() - 3, now.getDate()); break;
        case '6M': cutoff = new Date(now.getFullYear(), now.getMonth() - 6, now.getDate()); break;
        case '1Y': cutoff = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate()); break;
        default: return data;
    }
    return data.filter(function (d) { return new Date(d.date) >= cutoff; });
}

function getPredictionSubset(predictions, period) {
    if (!predictions || predictions.length === 0) return [];
    return predictions.slice(0, period);
}

function mergeLabels(hist, pred) {
    var seen = {};
    var result = [];
    function add(label) {
        if (!seen[label]) { seen[label] = true; result.push(label); }
    }
    hist.forEach(function (d) { add(d.date); });
    pred.forEach(function (d) { add(d.date); });
    return result;
}

function mapToLabel(data, label) {
    for (var i = 0; i < data.length; i++) {
        if (data[i].date === label) return data[i];
    }
    return null;
}

function buildDatasets(hist, pred) {
    var labels = mergeLabels(hist, pred);
    var datasets = [];

    if (hist.length > 0) {
        datasets.push({
            label: 'IHSG Historical',
            data: labels.map(function (l) {
                var d = mapToLabel(hist, l);
                return d ? d.close : null;
            }),
            borderColor: '#22c55e',
            backgroundColor: 'rgba(34, 197, 94, 0.12)',
            fill: true,
            pointRadius: 0,
            borderWidth: 2,
            tension: 0.1,
            spanGaps: false,
            order: 2,
        });
    }

    if (pred.length > 0) {
        var predValues = labels.map(function (l) {
            var d = mapToLabel(pred, l);
            return d ? d.yhat : null;
        });
        var upperValues = labels.map(function (l) {
            var d = mapToLabel(pred, l);
            return d ? d.yhat_upper : null;
        });
        var lowerValues = labels.map(function (l) {
            var d = mapToLabel(pred, l);
            return d ? d.yhat_lower : null;
        });

        datasets.push({
            label: 'Upper Bound',
            data: upperValues,
            borderColor: 'transparent',
            backgroundColor: 'transparent',
            pointRadius: 0,
            fill: '+1',
            order: 0,
        });
        datasets.push({
            label: 'Lower Bound',
            data: lowerValues,
            borderColor: 'transparent',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            pointRadius: 0,
            fill: false,
            order: 0,
        });
        datasets.push({
            label: 'Prediction',
            data: predValues,
            borderColor: '#f59e0b',
            backgroundColor: 'transparent',
            borderDash: [6, 4],
            borderWidth: 2,
            pointRadius: 0,
            fill: false,
            tension: 0.1,
            order: 1,
        });
    }

    return { labels: labels, datasets: datasets };
}

function initChart(historicalData, predictionData) {
    var ctx = document.getElementById('hybridChart');
    if (!ctx) return;

    var activeRange = '6M';
    var activePeriod = 30;

    function updateChart() {
        var hist = getDateRange(historicalData, activeRange);
        var pred = getPredictionSubset(predictionData, activePeriod);
        var result = buildDatasets(hist, pred);

        if (!hybridChart) {
            hybridChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: result.labels,
                    datasets: result.datasets,
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: 'index',
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            align: 'end',
                            labels: {
                                color: '#94a3b8',
                                boxWidth: 16,
                                padding: 16,
                                font: { family: 'JetBrains Mono, monospace', size: 11 },
                                usePointStyle: true,
                                pointStyle: 'line',
                            },
                        },
                        tooltip: {
                            backgroundColor: '#1a2338',
                            titleColor: '#f1f5f9',
                            bodyColor: '#94a3b8',
                            borderColor: '#1e293b',
                            borderWidth: 1,
                            padding: 12,
                            cornerRadius: 8,
                            titleFont: { family: 'Inter, sans-serif', size: 13 },
                            bodyFont: { family: 'JetBrains Mono, monospace', size: 12 },
                            callbacks: {
                                label: function (context) {
                                    var label = context.dataset.label || '';
                                    var val = context.parsed.y;
                                    if (label === 'Upper Bound' || label === 'Lower Bound') return null;
                                    return label + ': ' + (val !== null ? val.toFixed(2) : 'N/A');
                                },
                            },
                        },
                    },
                    scales: {
                        x: {
                            grid: { color: '#1e293b', drawBorder: false },
                            ticks: {
                                color: '#64748b',
                                font: { family: 'JetBrains Mono, monospace', size: 10 },
                                maxTicksLimit: 12,
                                autoSkip: true,
                            },
                        },
                        y: {
                            grid: { color: '#1e293b', drawBorder: false },
                            ticks: {
                                color: '#64748b',
                                font: { family: 'JetBrains Mono, monospace', size: 10 },
                                callback: function (value) { return value.toLocaleString(); },
                            },
                        },
                    },
                },
            });
        } else {
            hybridChart.data.labels = result.labels;
            hybridChart.data.datasets = result.datasets;
            hybridChart.update('none');
        }
    }

    updateChart();

    // Timeframe tabs
    document.querySelectorAll('.tab-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.tab-btn').forEach(function (b) {
                b.classList.remove('tab-active');
                b.classList.add('text-[#94a3b8]');
            });
            this.classList.add('tab-active');
            this.classList.remove('text-[#94a3b8]');

            activePeriod = parseInt(this.getAttribute('data-period'));
            updateChart();
        });
    });

    // Range selector
    document.querySelectorAll('.range-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.range-btn').forEach(function (b) {
                b.classList.remove('range-active');
            });
            this.classList.add('range-active');

            activeRange = this.getAttribute('data-range');
            updateChart();
        });
    });
}
