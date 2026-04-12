/**
 * Export module for ForecastIQ.
 * CSV download and data quality rendering.
 */

const ExportModule = {
    lastForecastData: null,
    lastAnomalyData: null,

    /**
     * Download forecast results as a CSV file.
     * @param {Object} data - Forecast response from the API
     */
    downloadForecastCSV(data) {
        if (!data) { App.showToast('Generate a forecast first', 'warning'); return; }

        const rows = [['Date', 'Forecast', 'Lower_Bound', 'Upper_Bound', 'Type']];
        // Historical fitted
        data.historical.dates.forEach((d, i) => {
            rows.push([d, data.historical.fitted[i]?.toFixed(2) ?? '', '', '', 'historical_fitted']);
        });
        // Forecast
        data.forecast.dates.forEach((d, i) => {
            rows.push([
                d,
                data.forecast.values[i]?.toFixed(2),
                data.forecast.lower_bound[i]?.toFixed(2),
                data.forecast.upper_bound[i]?.toFixed(2),
                'forecast',
            ]);
        });
        this._triggerDownload(rows, 'forecastiq_forecast.csv');
        App.showToast('Forecast CSV downloaded', 'success');
    },

    /**
     * Download anomaly detection results as CSV.
     * @param {Object} data - Anomaly response from the API
     */
    downloadAnomalyCSV(data) {
        if (!data) { App.showToast('Run anomaly detection first', 'warning'); return; }

        const rows = [['Date', 'Value', 'Severity', 'Direction', 'Deviation_Pct']];
        data.anomalies.forEach(a => {
            rows.push([a.date, a.value, a.severity, a.direction, a.deviation_pct]);
        });
        this._triggerDownload(rows, 'forecastiq_anomalies.csv');
        App.showToast('Anomalies CSV downloaded', 'success');
    },

    _triggerDownload(rows, filename) {
        const csv = rows.map(r => r.join(',')).join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url  = URL.createObjectURL(blob);
        const a    = Object.assign(document.createElement('a'), { href: url, download: filename });
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },
};

/**
 * Data Quality display module.
 */
const DataQuality = {
    async load(dataset, column) {
        if (!dataset) return;
        try {
            const res = await API.request('/api/data-quality', {
                method: 'POST',
                body: JSON.stringify({ dataset, value_column: column || undefined }),
            });
            this.render(res.data);
        } catch (e) {
            console.warn('Data quality check failed:', e.message);
        }
    },

    render(data) {
        const card = document.getElementById('data-health-card');
        if (!card) return;
        card.style.display = 'flex';

        const gradeColors = { success: 'var(--success)', info: 'var(--info)', warning: 'var(--warning)', danger: 'var(--danger)' };
        const color = gradeColors[data.grade_color] || 'var(--text-secondary)';

        document.getElementById('health-grade').textContent = data.grade;
        document.getElementById('health-grade').style.color = color;
        document.getElementById('health-score').textContent = `${data.health_score}/100`;
        document.getElementById('health-points').textContent = `${data.data_points} pts`;
        document.getElementById('health-completeness').textContent = `${data.completeness}%`;
        document.getElementById('health-seasonality').textContent = `${data.seasonality_strength}%`;
        document.getElementById('health-model').textContent = data.recommended_model;

        // Warnings
        const warnEl = document.getElementById('health-warnings');
        warnEl.innerHTML = '';
        (data.warnings || []).forEach(w => {
            const p = document.createElement('p');
            p.className = 'health-warning';
            p.textContent = `⚠ ${w}`;
            warnEl.appendChild(p);
        });
    },
};

/**
 * Alert threshold module — frontend-only warning banner.
 */
const ThresholdAlert = {
    check(forecastData, threshold) {
        const banner = document.getElementById('threshold-banner');
        if (!banner || !forecastData || !threshold) {
            if (banner) banner.style.display = 'none';
            return;
        }
        const thresholdVal = parseFloat(threshold);
        if (isNaN(thresholdVal)) { banner.style.display = 'none'; return; }

        const lower = forecastData.forecast?.lower_bound || [];
        const dates = forecastData.forecast?.dates || [];
        const breaches = lower
            .map((v, i) => ({ val: v, date: dates[i] }))
            .filter(x => x.val < thresholdVal);

        if (breaches.length > 0) {
            banner.style.display = 'flex';
            document.getElementById('threshold-text').textContent =
                `⚠ Early Warning: forecast lower bound drops below ${thresholdVal.toLocaleString()} ` +
                `in ${breaches.length} period(s) — earliest: ${breaches[0].date}`;
        } else {
            banner.style.display = 'none';
        }
    },
};
