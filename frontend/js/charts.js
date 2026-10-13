/**
 * Alphawise Chart.js & Visualization Engine
 * Theme-aware rendering for Institutional Bright Mode and Dark Mode.
 */

let frontierChartInstance = null;
let volatilityChartInstance = null;
let rollingVolChartInstance = null;

function getThemeConfig() {
  return {
    isDark: true,
    textColor: '#A0AAA1',
    tickColor: '#68746B',
    gridColor: 'rgba(39, 52, 42, 0.4)',
    tooltipBg: '#151C17',
    tooltipTitle: '#F1F4ED',
    tooltipBody: '#A0AAA1',
    tooltipBorder: '#27342A',
    frontierLine: '#C7F36B',
    frontierFill: 'rgba(199, 243, 107, 0.08)',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
  };
}

function getStarPointStyle(isDark) {
  if (typeof document === 'undefined') return 'star';
  try {
    const size = 20;
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    if (!ctx) return 'star';

    const cx = size / 2;
    const cy = size / 2;
    const spikes = 5;
    const outerRadius = 8;
    const innerRadius = 3.5;

    let rot = (Math.PI / 2) * 3;
    let x = cx;
    let y = cy;
    const step = Math.PI / spikes;

    ctx.beginPath();
    ctx.moveTo(cx, cy - outerRadius);
    for (let i = 0; i < spikes; i++) {
      x = cx + Math.cos(rot) * outerRadius;
      y = cy + Math.sin(rot) * outerRadius;
      ctx.lineTo(x, y);
      rot += step;

      x = cx + Math.cos(rot) * innerRadius;
      y = cy + Math.sin(rot) * innerRadius;
      ctx.lineTo(x, y);
      rot += step;
    }
    ctx.lineTo(cx, cy - outerRadius);
    ctx.closePath();

    // Solid filled star in acid green with dark crisp outline
    ctx.fillStyle = '#C7F36B';
    ctx.fill();

    ctx.lineWidth = 1.5;
    ctx.strokeStyle = '#080B0A';
    ctx.stroke();

    return canvas;
  } catch (e) {
    return 'star';
  }
}

export class ChartManager {
  /**
   * Renders the Efficient Frontier curve with highlighted portfolios and individual assets.
   */
  static renderEfficientFrontier(canvas, frontierPoints, currentPort, maxSharpePort, minVolPort, assetReturns, assetVols) {
    if (frontierChartInstance) {
      frontierChartInstance.destroy();
    }

    const theme = getThemeConfig();

    // Sort frontier by volatility
    const sortedFrontier = [...frontierPoints].sort((a, b) => a.volatility - b.volatility);
    const frontierScatter = sortedFrontier.map(p => ({
      x: +(p.volatility * 100).toFixed(2),
      y: +(p.expected_return * 100).toFixed(2),
      sharpe: p.sharpe_ratio
    }));

    // Individual assets
    const assetPoints = Object.keys(assetReturns).map(t => ({
      x: +((assetVols[t] || 0) * 100).toFixed(2),
      y: +((assetReturns[t] || 0) * 100).toFixed(2),
      ticker: t
    }));

    const datasets = [
      {
        label: 'Efficient Frontier Curve',
        data: frontierScatter,
        borderColor: theme.frontierLine,
        backgroundColor: theme.frontierFill,
        borderWidth: 2,
        fill: false,
        tension: 0.3,
        showLine: true,
        pointRadius: 2,
        pointHoverRadius: 6,
        type: 'scatter'
      },
      {
        label: 'Max Sharpe (Tangency Portfolio)',
        data: [{
          x: +(maxSharpePort.volatility * 100).toFixed(2),
          y: +(maxSharpePort.expected_return * 100).toFixed(2),
          sharpe: maxSharpePort.sharpe_ratio
        }],
        backgroundColor: '#C7F36B',
        borderColor: '#080B0A',
        borderWidth: 2,
        pointRadius: 9,
        pointHoverRadius: 12,
        pointStyle: getStarPointStyle(true),
        order: -1,
        type: 'scatter'
      },
      {
        label: 'Min Volatility Portfolio',
        data: [{
          x: +(minVolPort.volatility * 100).toFixed(2),
          y: +(minVolPort.expected_return * 100).toFixed(2),
          sharpe: minVolPort.sharpe_ratio
        }],
        backgroundColor: '#62B6F5',
        borderColor: '#080B0A',
        borderWidth: 2,
        pointRadius: 8,
        pointHoverRadius: 11,
        pointStyle: 'triangle',
        order: 0,
        type: 'scatter'
      },
      {
        label: 'Current Portfolio',
        data: [{
          x: +(currentPort.volatility * 100).toFixed(2),
          y: +(currentPort.expected_return * 100).toFixed(2),
          sharpe: currentPort.sharpe_ratio
        }],
        backgroundColor: '#FF647C',
        borderColor: '#080B0A',
        borderWidth: 2,
        pointRadius: 8,
        pointHoverRadius: 11,
        pointStyle: 'rectRot',
        order: 0,
        type: 'scatter'
      },
      {
        label: 'Individual Assets',
        data: assetPoints,
        backgroundColor: '#68746B',
        borderColor: '#27342A',
        borderWidth: 1.5,
        pointRadius: 5,
        pointHoverRadius: 8,
        order: 1,
        type: 'scatter'
      }
    ];

    frontierChartInstance = new Chart(canvas, {
      type: 'scatter',
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: theme.textColor,
              font: { family: theme.fontFamily, size: 12, weight: '600' },
              padding: 14,
              usePointStyle: true
            }
          },
          tooltip: {
            backgroundColor: theme.tooltipBg,
            titleColor: theme.tooltipTitle,
            bodyColor: theme.tooltipBody,
            borderColor: theme.tooltipBorder,
            borderWidth: 1,
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: function(ctx) {
                const raw = ctx.raw;
                if (raw.ticker) {
                  return ` ${raw.ticker}: Vol = ${raw.x}%, Return = ${raw.y}%`;
                }
                const label = ctx.dataset.label || '';
                const sharpe = raw.sharpe !== undefined ? `, Sharpe = ${raw.sharpe}` : '';
                return ` ${label}: Vol = ${raw.x}%, Return = ${raw.y}%${sharpe}`;
              }
            }
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Annualized Volatility (Risk) %',
              color: theme.textColor,
              font: { family: theme.fontFamily, size: 12, weight: '600' }
            },
            grid: { color: theme.gridColor },
            ticks: { color: theme.tickColor, font: { family: theme.fontFamily } }
          },
          y: {
            title: {
              display: true,
              text: 'Annualized Expected Return %',
              color: theme.textColor,
              font: { family: theme.fontFamily, size: 12, weight: '600' }
            },
            grid: { color: theme.gridColor },
            ticks: { color: theme.tickColor, font: { family: theme.fontFamily } }
          }
        }
      }
    });
  }

  /**
   * Renders the interactive Pearson Correlation Matrix Heatmap.
   */
  static renderCorrelationHeatmap(container, corrMatrix, tickers) {
    container.innerHTML = '';
    const table = document.createElement('table');
    table.className = 'heatmap-table';
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    // Header row
    const thead = document.createElement('thead');
    const headRow = document.createElement('tr');
    headRow.appendChild(document.createElement('th')); // empty corner
    tickers.forEach(t => {
      const th = document.createElement('th');
      th.textContent = t;
      headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    // Rows
    const tbody = document.createElement('tbody');
    tickers.forEach(rowTicker => {
      const tr = document.createElement('tr');
      const rowHeader = document.createElement('th');
      rowHeader.textContent = rowTicker;
      tr.appendChild(rowHeader);

      tickers.forEach(colTicker => {
        const td = document.createElement('td');
        const val = corrMatrix[rowTicker] ? corrMatrix[rowTicker][colTicker] : null;
        if (val !== null && val !== undefined) {
          td.textContent = (+val).toFixed(2);

          if (rowTicker === colTicker) {
            // Identity diagonal
            td.style.backgroundColor = 'rgba(199, 243, 107, 0.15)';
            td.style.color = '#C7F36B';
            td.style.fontWeight = '700';
          } else if (val > 0) {
            // Positive correlation (coral/rose): higher = less diversification
            const intensity = Math.min(1, Math.max(0, val));
            td.style.backgroundColor = `rgba(255, 100, 124, ${0.08 + intensity * 0.42})`;
            td.style.color = intensity > 0.4 ? '#FF8FA3' : '#F1F4ED';
          } else {
            // Negative correlation (green): strong diversification shelter
            const intensity = Math.min(1, Math.max(0, Math.abs(val)));
            td.style.backgroundColor = `rgba(155, 234, 69, ${0.08 + intensity * 0.42})`;
            td.style.color = '#9BEA45';
          }
          td.title = `${rowTicker} vs ${colTicker}: r = ${(+val).toFixed(3)}`;
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    container.appendChild(table);
  }

  /**
   * Renders individual asset annualized volatility bar chart.
   */
  static renderVolatilityBarChart(canvas, tickers, annualizedVols, currentVol, optVol) {
    if (volatilityChartInstance) {
      volatilityChartInstance.destroy();
    }

    const theme = getThemeConfig();

    const labels = [...tickers, 'Current Port', 'Max Sharpe Port'];
    const data = [
      ...tickers.map(t => +((annualizedVols[t] || 0) * 100).toFixed(2)),
      +(currentVol * 100).toFixed(2),
      +(optVol * 100).toFixed(2)
    ];

    const backgroundColors = [
      ...tickers.map(() => 'rgba(98, 182, 245, 0.35)'),
      'rgba(255, 100, 124, 0.65)',
      'rgba(199, 243, 107, 0.85)'
    ];

    const borderColors = [
      ...tickers.map(() => '#62B6F5'),
      '#FF647C',
      '#C7F36B'
    ];

    volatilityChartInstance = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Annualized Volatility (%)',
          data: data,
          backgroundColor: backgroundColors,
          borderColor: borderColors,
          borderWidth: 1.5,
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: theme.tooltipBg,
            titleColor: theme.tooltipTitle,
            bodyColor: theme.tooltipBody,
            borderColor: theme.tooltipBorder,
            borderWidth: 1,
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => ` Volatility: ${ctx.parsed.y}%`
            }
          }
        },
        scales: {
          x: {
            grid: { color: theme.gridColor },
            ticks: { color: theme.tickColor, font: { family: theme.fontFamily, weight: '600' } }
          },
          y: {
            title: {
              display: true,
              text: 'Volatility %',
              color: theme.textColor,
              font: { family: theme.fontFamily, size: 12, weight: '600' }
            },
            grid: { color: theme.gridColor },
            ticks: { color: theme.tickColor, font: { family: theme.fontFamily } }
          }
        }
      }
    });
  }

  /**
   * Renders 63-day rolling volatility time series chart.
   */
  static renderRollingVolatility(canvas, rollingMetrics) {
    if (rollingVolChartInstance) {
      rollingVolChartInstance.destroy();
    }

    const theme = getThemeConfig();

    const datasets = [
      {
        label: 'Current Portfolio Vol',
        data: rollingMetrics.current_portfolio_vol.map(v => v !== null ? +(v * 100).toFixed(2) : null),
        borderColor: '#FF647C',
        borderWidth: 2,
        tension: 0.25,
        pointRadius: 0
      },
      {
        label: 'Max Sharpe Portfolio Vol',
        data: rollingMetrics.max_sharpe_vol.map(v => v !== null ? +(v * 100).toFixed(2) : null),
        borderColor: '#C7F36B',
        borderWidth: 2,
        tension: 0.25,
        pointRadius: 0
      }
    ];

    rollingVolChartInstance = new Chart(canvas, {
      type: 'line',
      data: {
        labels: rollingMetrics.dates,
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: theme.textColor,
              font: { family: theme.fontFamily, size: 12, weight: '600' },
              padding: 14,
              usePointStyle: true
            }
          },
          tooltip: {
            backgroundColor: theme.tooltipBg,
            titleColor: theme.tooltipTitle,
            bodyColor: theme.tooltipBody,
            borderColor: theme.tooltipBorder,
            borderWidth: 1,
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y}%`
            }
          }
        },
        scales: {
          x: {
            grid: { color: theme.gridColor },
            ticks: { color: theme.tickColor, maxTicksLimit: 8, font: { family: theme.fontFamily } }
          },
          y: {
            title: {
              display: true,
              text: '63-Day Rolling Volatility %',
              color: theme.textColor,
              font: { family: theme.fontFamily, size: 12, weight: '600' }
            },
            grid: { color: theme.gridColor },
            ticks: { color: theme.tickColor, font: { family: theme.fontFamily } }
          }
        }
      }
    });
  }
}
