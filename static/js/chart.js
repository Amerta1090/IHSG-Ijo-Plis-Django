let hybridChart = null;
let sma20Visible = true;
let sma50Visible = true;

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

function mergeLabels(hist, pred, sma20, sma50) {
    var seen = {};
    var result = [];
    function add(label) {
        if (!seen[label]) { seen[label] = true; result.push(label); }
    }
    hist.forEach(function (d) { add(d.date); });
    pred.forEach(function (d) { add(d.date); });
    sma20.forEach(function (d) { add(d.date); });
    sma50.forEach(function (d) { add(d.date); });
    return result;
}

function mapToLabel(data, label) {
    for (var i = 0; i < data.length; i++) {
        if (data[i].date === label) return data[i];
    }
    return null;
}

function buildDatasets(hist, pred, sma20, sma50, marketConfig) {
    var labels = mergeLabels(hist, pred, sma20, sma50);
    var datasets = [];
    if (!marketConfig) {
        marketConfig = {
            histLabel: 'Historical',
            apiEndpoint: '/api/metrics.json',
            decompEndpoint: '/api/decomposition.json',
            colors: {
                historical: '#00ff88',
                historicalFill: 'rgba(0, 255, 136, 0.12)',
                prediction: '#f59e0b',
                band: 'rgba(245, 158, 11, 0.1)',
            },
        };
    }
    var colors = marketConfig.colors;

    if (hist.length > 0) {
        datasets.push({
            label: marketConfig.histLabel,
            data: labels.map(function (l) {
                var d = mapToLabel(hist, l);
                return d ? d.close : null;
            }),
            borderColor: colors.historical,
            backgroundColor: colors.historicalFill,
            fill: true,
            pointRadius: 0,
            borderWidth: 2,
            tension: 0,
            spanGaps: false,
            order: 4,
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
            label: 'Lower Bound',
            data: lowerValues,
            borderColor: 'transparent',
            backgroundColor: colors.band,
            pointRadius: 0,
            fill: '+1',
            order: 0,
        });
        datasets.push({
            label: 'Upper Bound',
            data: upperValues,
            borderColor: 'transparent',
            backgroundColor: 'transparent',
            pointRadius: 0,
            fill: false,
            order: 0,
        });
        datasets.push({
            label: 'Prediction',
            data: predValues,
            borderColor: colors.prediction,
            backgroundColor: 'transparent',
            borderDash: [6, 4],
            borderWidth: 2,
            pointRadius: 0,
            fill: false,
            tension: 0,
            order: 3,
        });
    }

    if (sma20.length > 0 && sma20Visible) {
        datasets.push({
            label: 'SMA 20',
            data: labels.map(function (l) {
                var d = mapToLabel(sma20, l);
                return d ? d.value : null;
            }),
            borderColor: '#3b82f6',
            backgroundColor: 'transparent',
            borderWidth: 1.5,
            borderDash: [3, 3],
            pointRadius: 0,
            tension: 0,
            order: 2,
        });
    }

    if (sma50.length > 0 && sma50Visible) {
        datasets.push({
            label: 'SMA 50',
            data: labels.map(function (l) {
                var d = mapToLabel(sma50, l);
                return d ? d.value : null;
            }),
            borderColor: '#a855f7',
            backgroundColor: 'transparent',
            borderWidth: 1.5,
            borderDash: [3, 3],
            pointRadius: 0,
            tension: 0,
            order: 1,
        });
    }

    return { labels: labels, datasets: datasets };
}

function initChart(historicalData, predictionData, sma20Data, sma50Data, marketConfig) {
    var ctx = document.getElementById('hybridChart');
    if (!ctx) return;

    var activeRange = '6M';
    var activePeriod = 30;

    sma20Data = sma20Data || [];
    sma50Data = sma50Data || [];

    function updateChart() {
        var hist = getDateRange(historicalData, activeRange);
        var pred = getPredictionSubset(predictionData, activePeriod);
        var sma20 = getDateRange(sma20Data, activeRange);
        var sma50 = getDateRange(sma50Data, activeRange);
        var result = buildDatasets(hist, pred, sma20, sma50, marketConfig);

        if (!hybridChart) {
            hybridChart = new Chart(ctx, {
                type: 'line',
                data: { labels: result.labels, datasets: result.datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { intersect: false, mode: 'index' },
                    plugins: {
                        legend: {
                            display: true, position: 'top', align: 'end',
                            labels: {
                                color: '#94a3b8', boxWidth: 16, padding: 16,
                                font: { family: 'JetBrains Mono, monospace', size: 11 },
                                usePointStyle: true, pointStyle: 'line',
                            },
                        },
                        tooltip: {
                            backgroundColor: '#1a1a1a', titleColor: '#f1f5f9',
                            bodyColor: '#94a3b8', borderColor: '#2a2a2a',
                            borderWidth: 1, padding: 12, cornerRadius: 8,
                            titleFont: { family: 'Outfit, sans-serif', size: 13 },
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
                            grid: { color: '#2a2a2a', drawBorder: false },
                            ticks: {
                                color: '#64748b', font: { family: 'JetBrains Mono, monospace', size: 10 },
                                maxTicksLimit: 12, autoSkip: true,
                            },
                        },
                        y: {
                            grid: { color: '#2a2a2a', drawBorder: false },
                            ticks: {
                                color: '#64748b', font: { family: 'JetBrains Mono, monospace', size: 10 },
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

    document.querySelectorAll('.sma-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var sma = this.getAttribute('data-sma');
            if (sma === '20') {
                sma20Visible = !sma20Visible;
                this.classList.toggle('sma-active');
            } else {
                sma50Visible = !sma50Visible;
                this.classList.toggle('sma-active');
            }
            updateChart();
        });
    });
}