function animateCountUp(el) {
    const target = parseFloat(el.getAttribute('data-value')) || 0;
    const decimals = parseInt(el.getAttribute('data-decimals')) || 0;
    const duration = 1200;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = target * eased;
        el.textContent = current.toFixed(decimals);
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            el.textContent = target.toFixed(decimals);
        }
    }
    requestAnimationFrame(update);
}

function initMetrics(historicalData, predictionData) {
    document.querySelectorAll('.count-up').forEach(animateCountUp);
}
