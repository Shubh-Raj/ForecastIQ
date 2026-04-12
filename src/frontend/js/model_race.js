/**
 * Model comparison module for ForecastIQ.
 * Runs ETS vs ARIMA vs Moving Average and renders a leaderboard.
 */

const ModelRace = {
    init() {
        const btn = document.getElementById('btn-model-race');
        if (btn) btn.addEventListener('click', () => this.run());
    },

    async run() {
        const dataset    = document.getElementById('dataset-select').value;
        const column     = document.getElementById('column-select').value;
        const horizon    = parseInt(document.getElementById('forecast-horizon').value || '4');
        const confidence = parseFloat(document.getElementById('forecast-confidence').value || '0.95');

        if (!dataset) { App.showToast('Select a dataset first', 'warning'); return; }

        App.showLoading('Running model race...');
        try {
            const res = await API.request('/api/model-comparison', {
                method: 'POST',
                body: JSON.stringify({ dataset, value_column: column || undefined, horizon, confidence }),
            });
            this.render(res.data);
            App.showToast(`Winner: ${res.data.winner}`, 'success');
        } catch (e) {
            App.showToast(e.message, 'error');
        } finally {
            App.hideLoading();
        }
    },

    render(data) {
        const section = document.getElementById('model-race-section');
        section.style.display = 'block';

        // Leaderboard table
        const tbody = document.getElementById('leaderboard-body');
        tbody.innerHTML = '';
        data.leaderboard.forEach(m => {
            const tr = document.createElement('tr');
            tr.className = m.is_winner ? 'leaderboard-winner' : '';
            tr.innerHTML = `
                <td>${m.rank}</td>
                <td>${m.is_winner ? '🏆 ' : ''}${m.name}</td>
                <td style="color:${m.mape < 10 ? 'var(--success)' : m.mape < 20 ? 'var(--warning)' : 'var(--danger)'}">${m.mape}%</td>
                <td>${m.rmse.toLocaleString()}</td>
                <td class="model-desc">${m.description}</td>`;
            tbody.appendChild(tr);
        });

        // Multi-model chart
        const hDates = data.historical_dates;
        const fDates = data.forecast_dates;
        const allDates = [...hDates, ...fDates];
        const histVals = data.historical_values.concat(new Array(fDates.length).fill(null));

        const colors = [Charts.colors.success, Charts.colors.secondary, Charts.colors.warning];
        const modelDatasets = data.leaderboard.map((m, i) => {
            const mdl = data.models[m.model];
            const vals = new Array(hDates.length).fill(null).concat(mdl.forecast);
            vals[hDates.length - 1] = data.historical_values[data.historical_values.length - 1];
            return {
                label: m.is_winner ? `${m.model} (winner)` : m.model,
                data: vals,
                borderColor: colors[i] || Charts.colors.cyan,
                backgroundColor: 'transparent',
                borderWidth: m.is_winner ? 3 : 1.5,
                borderDash: m.is_winner ? [] : [5, 4],
                pointRadius: m.is_winner ? 4 : 2,
                tension: 0.3,
            };
        });

        Charts.createChart('model-race-chart', {
            type: 'line',
            data: {
                labels: allDates,
                datasets: [
                    { label: 'Historical', data: histVals, borderColor: Charts.colors.primary, backgroundColor: Charts.colors.primaryLight, fill: true, borderWidth: 2, pointRadius: 1, tension: 0.3 },
                    ...modelDatasets,
                ]
            },
            options: Charts.getDefaultOptions(),
        });
    }
};
