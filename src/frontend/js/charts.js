/**
 * Chart rendering utilities for ForecastIQ.
 * 
 * Provides reusable chart configurations and helpers
 * for rendering time-series data with Chart.js.
 */

const Charts = {
    /** Store chart instances for cleanup */
    instances: {},

    /** Shared color palette */
    colors: {
        primary: '#6366f1',
        primaryLight: 'rgba(99, 102, 241, 0.15)',
        secondary: '#8b5cf6',
        secondaryLight: 'rgba(139, 92, 246, 0.15)',
        success: '#22c55e',
        successLight: 'rgba(34, 197, 94, 0.15)',
        warning: '#f59e0b',
        warningLight: 'rgba(245, 158, 11, 0.15)',
        danger: '#ef4444',
        dangerLight: 'rgba(239, 68, 68, 0.15)',
        info: '#3b82f6',
        infoLight: 'rgba(59, 130, 246, 0.15)',
        cyan: '#06b6d4',
        cyanLight: 'rgba(6, 182, 212, 0.15)',
        grid: 'rgba(255, 255, 255, 0.05)',
        gridLabel: 'rgba(255, 255, 255, 0.4)',
        tooltip: 'rgba(17, 18, 32, 0.95)',
    },

    /**
     * Get default chart options for a dark-themed time series chart.
     * @param {string} title - Chart title
     * @returns {Object} Chart.js options
     */
    getDefaultOptions(title = '') {
        return {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: !!title,
                    text: title,
                    color: '#f0f0f5',
                    font: { size: 14, weight: '600', family: 'Inter' },
                    padding: { bottom: 16 },
                },
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: {
                        color: '#9ca3af',
                        font: { size: 12, family: 'Inter' },
                        usePointStyle: true,
                        pointStyle: 'circle',
                        padding: 16,
                    },
                },
                tooltip: {
                    backgroundColor: this.colors.tooltip,
                    titleColor: '#f0f0f5',
                    bodyColor: '#9ca3af',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    titleFont: { size: 13, weight: '600', family: 'Inter' },
                    bodyFont: { size: 12, family: 'Inter' },
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y;
                            if (value !== null && value !== undefined) {
                                return `${label}: ${value.toLocaleString(undefined, { maximumFractionDigits: 1 })}`;
                            }
                            return label;
                        },
                    },
                },
            },
            scales: {
                x: {
                    grid: { color: this.colors.grid, drawBorder: false },
                    ticks: {
                        color: this.colors.gridLabel,
                        font: { size: 11, family: 'Inter' },
                        maxRotation: 45,
                        maxTicksLimit: 15,
                    },
                },
                y: {
                    grid: { color: this.colors.grid, drawBorder: false },
                    ticks: {
                        color: this.colors.gridLabel,
                        font: { size: 11, family: 'Inter' },
                        callback: function(value) {
                            return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
                        },
                    },
                },
            },
            animation: {
                duration: 800,
                easing: 'easeOutQuart',
            },
        };
    },

    /**
     * Create or update a chart instance.
     * @param {string} canvasId - Canvas element ID
     * @param {Object} config - Chart.js configuration
     * @returns {Chart} Chart instance
     */
    createChart(canvasId, config) {
        // Destroy existing chart on same canvas
        if (this.instances[canvasId]) {
            this.instances[canvasId].destroy();
        }

        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas element #${canvasId} not found`);
            return null;
        }

        canvas.style.display = 'block';
        const chart = new Chart(canvas.getContext('2d'), config);
        this.instances[canvasId] = chart;
        return chart;
    },

    /**
     * Create a confidence band (filled area) dataset.
     * @param {string} label - Dataset label
     * @param {Array<number>} upperData - Upper bound values
     * @param {Array<number>} lowerData - Lower bound values
     * @param {string} color - Fill color (with alpha)
     * @param {number} startIndex - Index where the band starts
     * @param {number} totalLength - Total number of data points
     * @returns {Array<Object>} Two datasets forming the band
     */
    createConfidenceBand(label, upperData, lowerData, color, startIndex, totalLength) {
        const upperFull = new Array(startIndex).fill(null).concat(upperData);
        const lowerFull = new Array(startIndex).fill(null).concat(lowerData);

        return [
            {
                label: `${label} (Upper)`,
                data: upperFull,
                borderColor: 'transparent',
                backgroundColor: color,
                fill: '+1',
                pointRadius: 0,
                tension: 0.3,
                order: 10,
            },
            {
                label: `${label} (Lower)`,
                data: lowerFull,
                borderColor: 'transparent',
                backgroundColor: 'transparent',
                fill: false,
                pointRadius: 0,
                tension: 0.3,
                order: 10,
            },
        ];
    },

    /**
     * Format a number for display in charts.
     * @param {number} value - Number to format
     * @param {number} decimals - Decimal places
     * @returns {string} Formatted number
     */
    formatNumber(value, decimals = 1) {
        if (value === null || value === undefined) return '—';
        if (Math.abs(value) >= 1e6) return (value / 1e6).toFixed(decimals) + 'M';
        if (Math.abs(value) >= 1e3) return (value / 1e3).toFixed(decimals) + 'K';
        return value.toFixed(decimals);
    },

    /**
     * Destroy a chart instance.
     * @param {string} canvasId - Canvas element ID
     */
    destroyChart(canvasId) {
        if (this.instances[canvasId]) {
            this.instances[canvasId].destroy();
            delete this.instances[canvasId];
        }
    },
};
