import { ApiClient } from './api.js?v=2.5.5';
import { ChartManager } from './charts.js?v=2.5.5';

// Predefined portfolio templates for hackathon showcase
const PRESETS = {
  tech: {
    name: 'Tech Megacaps 🔥',
    tickers: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA'],
    weights: [0.25, 0.25, 0.20, 0.15, 0.15]
  },
  balanced: {
    name: 'Classic 60/40',
    tickers: ['SPY', 'QQQ', 'BND', 'GLD'],
    weights: [0.35, 0.25, 0.30, 0.10]
  },
  allweather: {
    name: 'All-Weather Diversified',
    tickers: ['VTI', 'TLT', 'IEF', 'GLD', 'DBC'],
    weights: [0.30, 0.40, 0.15, 0.075, 0.075]
  },
  inflation: {
    name: 'Inflation Shield',
    tickers: ['XLE', 'GLD', 'TIP', 'VTI'],
    weights: [0.35, 0.30, 0.20, 0.15]
  }
};

// What-If Sandbox Candidate Catalog
const WHATIF_CATALOG = {
  gld: {
    ticker: 'GLD',
    weight: 10,
    name: 'Selected: +10% Gold (GLD)',
    sharpeDelta: '+0.14 Sharpe',
    volDelta: '-2.1% Risk',
    enbDelta: '+0.7 Bets',
    positiveSharpe: true,
    positiveVol: true,
    explanation: 'Adding Gold introduces non-correlated commodity risk, offsetting equity valuation compressions and dampening portfolio drawdown during liquidity crunches.'
  },
  tlt: {
    ticker: 'TLT',
    weight: 15,
    name: 'Selected: +15% Long Treasuries (TLT)',
    sharpeDelta: '+0.18 Sharpe',
    volDelta: '-3.4% Risk',
    enbDelta: '+1.1 Bets',
    positiveSharpe: true,
    positiveVol: true,
    explanation: 'Long-duration sovereign debt acts as a classic flight-to-safety duration hedge, absorbing equity shocks during disinflationary market panics.'
  },
  btc: {
    ticker: 'BTC-USD',
    weight: 5,
    name: 'Selected: +5% Bitcoin (BTC-USD)',
    sharpeDelta: '+0.22 Sharpe',
    volDelta: '+1.2% Risk',
    enbDelta: '+0.5 Bets',
    positiveSharpe: true,
    positiveVol: false,
    explanation: 'A modest 5% digital gold allocation enhances expected asymmetric upside while maintaining contained portfolio-level variance.'
  },
  cash: {
    ticker: 'BIL',
    weight: 15,
    name: 'Selected: +15% Cash T-Bills (BIL)',
    sharpeDelta: '+0.06 Sharpe',
    volDelta: '-3.8% Risk',
    enbDelta: '+0.3 Bets',
    positiveSharpe: true,
    positiveVol: true,
    explanation: 'Short-term Treasury bills provide pure risk-free yield with zero duration risk, drastically lowering tail volatility at the expense of upside participation.'
  }
};

let currentPortfolioData = null;
let activeStressScenarioId = null;
let activeWhatIfKey = 'gld';

// Initialize DOM
document.addEventListener('DOMContentLoaded', () => {
  setupTheme();
  setupEventListeners();
  loadPreset('tech');
  checkBackendHealth();
  updateWhatIfCard('gld');
});

function setupTheme() {
  let savedTheme = 'dark';
  try {
    savedTheme = localStorage.getItem('alphawise_theme') || 'dark';
  } catch (e) {
    savedTheme = 'dark';
  }
  applyTheme(savedTheme);

  window.toggleTheme = function() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'terminal' : 'dark';
    applyTheme(next);
    try {
      localStorage.setItem('alphawise_theme', next);
    } catch (e) {}

    // If data is already rendered, refresh charts for theme palette
    if (currentPortfolioData) {
      try {
        renderResults(currentPortfolioData);
      } catch (e) {}
    }
  };

  const toggleBtn = document.getElementById('btn-theme-toggle');
  if (toggleBtn) {
    toggleBtn.onclick = function(e) {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      window.toggleTheme();
    };
  }
}

function applyTheme(theme) {
  // Institutional Terminal strictly enforces dark aesthetic
  const t = theme === 'terminal' ? 'terminal' : 'dark';
  document.documentElement.setAttribute('data-theme', t);
  if (document.body) {
    document.body.setAttribute('data-theme', t);
  }
  const icon = document.getElementById('theme-toggle-icon');
  const label = document.getElementById('theme-toggle-text');
  if (icon && label) {
    icon.textContent = '🌙';
    label.textContent = t === 'terminal' ? 'Terminal Mode' : 'Dark Mode';
  }
}

async function checkBackendHealth() {
  const statusText = document.getElementById('backend-status-text');
  const dot = document.getElementById('backend-dot');
  const healthy = await ApiClient.checkHealth();
  if (healthy) {
    statusText.textContent = 'Engine Active';
    dot.style.backgroundColor = 'var(--accent-emerald)';
  } else {
    statusText.textContent = 'Engine Offline (Start Backend)';
    dot.style.backgroundColor = 'var(--accent-amber)';
  }
}

function setupEventListeners() {
  // Preset buttons
  document.querySelectorAll('[data-preset]').forEach(btn => {
    btn.addEventListener('click', () => {
      const presetKey = btn.getAttribute('data-preset');
      loadPreset(presetKey);
    });
  });

  // Equalize Weights button
  const equalBtn = document.getElementById('btn-equal-weight');
  if (equalBtn) {
    equalBtn.addEventListener('click', () => {
      const rows = document.querySelectorAll('#asset-tbody tr');
      if (rows.length === 0) return;
      const equalWeight = (100.0 / rows.length).toFixed(1);
      rows.forEach(r => {
        const input = r.querySelector('.weight-input');
        if (input) input.value = equalWeight;
      });
      updateWeightTotal();
    });
  }

  // Clear All button
  const clearBtn = document.getElementById('btn-clear-assets');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      const tbody = document.getElementById('asset-tbody');
      tbody.innerHTML = '';
      updateWeightTotal();
    });
  }

  // Quick ticker suggestion chips
  document.querySelectorAll('[data-quick-ticker]').forEach(chip => {
    chip.addEventListener('click', () => {
      const ticker = chip.getAttribute('data-quick-ticker');
      if (ticker) {
        addAssetRow(ticker, 0);
        updateWeightTotal();
        // Focus newly added input
        const rows = document.querySelectorAll('#asset-tbody tr');
        const lastRow = rows[rows.length - 1];
        if (lastRow) {
          const input = lastRow.querySelector('.weight-input');
          if (input) {
            input.focus();
            input.select();
          }
        }
      }
    });
  });

  // Add Asset button
  document.getElementById('btn-add-asset').addEventListener('click', () => {
    const input = document.getElementById('new-ticker-input');
    const ticker = input.value.trim().toUpperCase();
    if (ticker) {
      addAssetRow(ticker, 0);
      input.value = '';
      updateWeightTotal();
    }
  });

  // Enter key on ticker input
  document.getElementById('new-ticker-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      document.getElementById('btn-add-asset').click();
    }
  });

  // Run Optimization Form Submit
  document.getElementById('optimization-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    await executeOptimization();
  });

  // Apply Weights Button
  document.getElementById('btn-apply-weights').addEventListener('click', () => {
    if (!currentPortfolioData) return;
    const optimalWeights = currentPortfolioData.max_sharpe_portfolio.weights;
    applyWeightsToInputs(optimalWeights);
    const btn = document.getElementById('btn-apply-weights');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span>✓ Applied to Portfolio!</span>';
    setTimeout(() => { btn.innerHTML = originalText; }, 2000);
  });

  // Copy Trade Ticket Button
  document.getElementById('btn-copy-ticket').addEventListener('click', copyTradeTicket);

  // Export Tear Sheet Button (PDF / Print)
  document.getElementById('btn-export-pdf').addEventListener('click', () => {
    window.print();
  });

  // AI Hub Mode Switcher (Institutional Memo vs Roast Mode)
  const btnInst = document.getElementById('btn-toggle-institutional');
  const btnRoast = document.getElementById('btn-toggle-roast');
  const paneInst = document.getElementById('pane-memo-institutional');
  const paneRoast = document.getElementById('pane-memo-roast');

  btnInst.addEventListener('click', () => {
    btnInst.classList.add('active');
    btnRoast.classList.remove('active');
    paneInst.classList.remove('hidden');
    paneRoast.classList.add('hidden');
  });

  btnRoast.addEventListener('click', () => {
    btnRoast.classList.add('active');
    btnInst.classList.remove('active');
    paneRoast.classList.remove('hidden');
    paneInst.classList.add('hidden');
  });

  // Chart Tabs
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const tab = btn.getAttribute('data-tab');
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.add('hidden'));
      const activePane = document.getElementById(`pane-${tab}`);
      if (activePane) activePane.classList.remove('hidden');
    });
  });

  // What-If Sandbox Pills
  document.querySelectorAll('.whatif-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.whatif-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const key = pill.getAttribute('data-whatif');
      activeWhatIfKey = key;
      updateWhatIfCard(key);
    });
  });

  // What-If Inject Button
  document.getElementById('btn-inject-asset').addEventListener('click', injectWhatIfAsset);

  // AI Commentary Re-roll Button
  const btnRegenAi = document.getElementById('btn-regen-ai');
  if (btnRegenAi) {
    btnRegenAi.addEventListener('click', handleRegenerateAiMemo);
  }

  // Copilot Widget Events
  setupCopilotEvents();
}

function loadPreset(presetKey) {
  const preset = PRESETS[presetKey];
  if (!preset) return;

  const tableBody = document.getElementById('asset-tbody');
  tableBody.innerHTML = '';

  preset.tickers.forEach((ticker, idx) => {
    addAssetRow(ticker, preset.weights[idx] * 100);
  });

  updateWeightTotal();
}

function addAssetRow(ticker, weightPct) {
  const tbody = document.getElementById('asset-tbody');
  
  const existing = Array.from(tbody.querySelectorAll('.ticker-name')).map(el => el.textContent);
  if (existing.includes(ticker)) return;

  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td><strong class="ticker-name ticker-name-badge">${ticker}</strong></td>
    <td style="text-align: right;">
      <div class="weight-input-container">
        <input type="number" class="weight-input" min="0" max="100" step="any" value="${weightPct.toFixed(1)}">
        <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600;">%</span>
      </div>
    </td>
    <td style="text-align: center;">
      <button type="button" class="btn-remove-asset" title="Remove asset">&times;</button>
    </td>
  `;

  const weightInput = tr.querySelector('.weight-input');
  weightInput.addEventListener('input', updateWeightTotal);

  const removeBtn = tr.querySelector('.btn-remove-asset');
  removeBtn.addEventListener('click', () => {
    tr.remove();
    updateWeightTotal();
  });

  tbody.appendChild(tr);
}

function updateWeightTotal() {
  const inputs = document.querySelectorAll('.weight-input');
  let sum = 0;
  inputs.forEach(inp => {
    sum += parseFloat(inp.value) || 0;
  });

  const totalEl = document.getElementById('weight-total-display');
  totalEl.textContent = `${sum.toFixed(1)}%`;

  // Update visual progress meter
  const progressBar = document.getElementById('weight-progress-bar');
  const statusBadge = document.getElementById('weight-status-badge');
  const clamped = Math.min(100, Math.max(0, sum));

  if (progressBar) {
    progressBar.style.width = `${clamped}%`;
  }

  const isBalanced = Math.abs(sum - 100) < 0.1;
  const isOver = sum > 100.1;

  if (isBalanced) {
    totalEl.className = 'weight-valid';
    if (progressBar) progressBar.style.backgroundColor = 'var(--accent-emerald)';
    if (statusBadge) {
      statusBadge.textContent = 'Balanced';
      statusBadge.className = 'status-tag valid';
    }
  } else if (isOver) {
    totalEl.className = 'weight-invalid';
    if (progressBar) progressBar.style.backgroundColor = 'var(--accent-rose)';
    if (statusBadge) {
      statusBadge.textContent = `${(sum - 100).toFixed(1)}% Over`;
      statusBadge.className = 'status-tag invalid';
    }
  } else {
    totalEl.className = 'weight-invalid';
    if (progressBar) progressBar.style.backgroundColor = 'var(--accent-amber)';
    if (statusBadge) {
      statusBadge.textContent = `${(100 - sum).toFixed(1)}% Left`;
      statusBadge.className = 'status-tag pending';
    }
  }
}

function applyWeightsToInputs(weightsMap) {
  const rows = document.querySelectorAll('#asset-tbody tr');
  rows.forEach(row => {
    const ticker = row.querySelector('.ticker-name').textContent.trim();
    const input = row.querySelector('.weight-input');
    if (weightsMap[ticker] !== undefined) {
      input.value = (weightsMap[ticker] * 100).toFixed(1);
    }
  });
  updateWeightTotal();
}

async function executeOptimization() {
  const submitBtn = document.getElementById('btn-optimize-submit');
  const spinner = document.getElementById('optimize-spinner');
  const errorAlert = document.getElementById('error-alert');

  errorAlert.classList.add('hidden');
  errorAlert.textContent = '';
  submitBtn.disabled = true;
  spinner.classList.remove('hidden');

  try {
    const rows = document.querySelectorAll('#asset-tbody tr');
    const tickers = [];
    const currentWeights = {};

    rows.forEach(row => {
      const ticker = row.querySelector('.ticker-name').textContent.trim();
      const val = parseFloat(row.querySelector('.weight-input').value) || 0;
      tickers.push(ticker);
      currentWeights[ticker] = val / 100.0;
    });

    if (tickers.length < 2) {
      throw new Error('Please enter at least 2 distinct assets to run portfolio optimization.');
    }

    const lookbackYears = parseInt(document.getElementById('input-lookback').value, 10) || 3;
    const riskFreeRate = (parseFloat(document.getElementById('input-rf').value) || 4.5) / 100.0;
    const maxWeight = (parseFloat(document.getElementById('input-max-weight').value) || 100.0) / 100.0;

    const payload = {
      tickers,
      current_weights: currentWeights,
      lookback_years: lookbackYears,
      risk_free_rate: riskFreeRate,
      max_asset_weight: maxWeight,
      frontier_points: 35
    };

    const data = await ApiClient.optimizePortfolio(payload);
    currentPortfolioData = data;
    renderResults(data);
    updateCopilotContextBadge();

  } catch (err) {
    errorAlert.textContent = err.message || 'An error occurred during optimization.';
    errorAlert.classList.remove('hidden');
  } finally {
    submitBtn.disabled = false;
    spinner.classList.add('hidden');
  }
}

function renderResults(data) {
  document.getElementById('results-section').classList.remove('hidden');

  const curr = data.current_portfolio;
  const opt = data.max_sharpe_portfolio;
  const minVol = data.min_volatility_portfolio;
  const risk = data.risk_metrics;

  // 1. Metric Cards
  document.getElementById('card-curr-sharpe').textContent = curr.sharpe_ratio.toFixed(2);
  document.getElementById('card-opt-sharpe').textContent = opt.sharpe_ratio.toFixed(2);
  
  const sharpeDelta = opt.sharpe_ratio - curr.sharpe_ratio;
  const sharpeBadge = document.getElementById('badge-sharpe-delta');
  sharpeBadge.textContent = `${sharpeDelta >= 0 ? '+' : ''}${sharpeDelta.toFixed(2)} Δ`;
  sharpeBadge.className = `delta-badge ${sharpeDelta >= 0 ? 'positive' : 'negative'}`;

  document.getElementById('card-opt-vol').textContent = `${(opt.volatility * 100).toFixed(1)}%`;
  const volDelta = (opt.volatility - curr.volatility) * 100;
  const volBadge = document.getElementById('badge-vol-delta');
  volBadge.textContent = `${volDelta <= 0 ? '' : '+'}${volDelta.toFixed(1)}% vs current`;
  volBadge.className = `delta-badge ${volDelta <= 0 ? 'positive' : 'negative'}`;

  document.getElementById('card-opt-return').textContent = `${(opt.expected_return * 100).toFixed(1)}%`;
  const retDelta = (opt.expected_return - curr.expected_return) * 100;
  const retBadge = document.getElementById('badge-return-delta');
  retBadge.textContent = `${retDelta >= 0 ? '+' : ''}${retDelta.toFixed(1)}% vs current`;
  retBadge.className = `delta-badge ${retDelta >= 0 ? 'positive' : 'negative'}`;

  // Spectral Effective Number of Bets
  document.getElementById('card-effective-bets').textContent = risk.effective_bets.toFixed(2);
  document.getElementById('card-bets-total').textContent = `out of ${data.metadata.tickers.length} assets`;

  // 2. Render AI CIO Intelligence & Health Score
  if (data.health_score) {
    renderHealthScore(data.health_score);
  }
  if (data.ai_commentary) {
    renderAiCommentary(data.ai_commentary);
  }

  // 3. Render Macro Crisis Stress-Test Simulator
  if (data.stress_tests && data.stress_tests.length > 0) {
    renderStressTests(data.stress_tests);
  }

  // 4. Render Charts
  const frontierCanvas = document.getElementById('frontier-canvas');
  ChartManager.renderEfficientFrontier(
    frontierCanvas,
    data.efficient_frontier,
    curr,
    opt,
    minVol,
    risk.annualized_returns,
    risk.annualized_volatilities
  );

  const heatmapContainer = document.getElementById('heatmap-container');
  ChartManager.renderCorrelationHeatmap(
    heatmapContainer,
    risk.correlation_matrix,
    data.metadata.tickers
  );

  const volCanvas = document.getElementById('volatility-canvas');
  ChartManager.renderVolatilityBarChart(
    volCanvas,
    data.metadata.tickers,
    risk.annualized_volatilities,
    curr.volatility,
    opt.volatility
  );

  const rollingCanvas = document.getElementById('rolling-canvas');
  ChartManager.renderRollingVolatility(rollingCanvas, data.rolling_metrics);

  // 5. Rebalance Table
  renderRebalanceTable(data.rebalance_actions);
}

function renderHealthScore(health) {
  document.getElementById('health-score-value').textContent = health.score;
  const gradeBadge = document.getElementById('health-grade-badge');
  gradeBadge.textContent = `GRADE ${health.grade}`;
  
  const g = health.grade.toLowerCase().charAt(0);
  gradeBadge.className = `score-badge grade-${g}`;

  document.getElementById('health-rating-title').textContent = health.rating;

  const comps = health.component_scores;
  if (comps) {
    document.getElementById('score-div-val').textContent = `${comps.diversification}/30`;
    document.getElementById('bar-div-fill').style.width = `${(comps.diversification / 30) * 100}%`;

    document.getElementById('score-eff-val').textContent = `${comps.sharpe_efficiency}/30`;
    document.getElementById('bar-eff-fill').style.width = `${(comps.sharpe_efficiency / 30) * 100}%`;

    document.getElementById('score-vol-val').textContent = `${comps.volatility_discipline}/20`;
    document.getElementById('bar-vol-fill').style.width = `${(comps.volatility_discipline / 20) * 100}%`;

    document.getElementById('score-tail-val').textContent = `${comps.tail_resilience}/20`;
    document.getElementById('bar-tail-fill').style.width = `${(comps.tail_resilience / 20) * 100}%`;
  }
}

function renderAiCommentary(commentary) {
  const inst = commentary.institutional_memo;
  if (inst) {
    document.getElementById('memo-exec-summary').textContent = inst.executive_summary;
    document.getElementById('memo-div-analysis').textContent = inst.diversification_analysis;
    document.getElementById('memo-tail-warning').textContent = inst.risk_tail_warning;
    document.getElementById('memo-rebalance-rationale').textContent = inst.rebalance_rationale;
  }

  const roast = commentary.roast_memo;
  if (roast) {
    document.getElementById('roast-spicy-pill').textContent = roast.spicy_rating;
    document.getElementById('roast-headline-text').textContent = roast.headline;
    document.getElementById('roast-body-text').textContent = roast.roast_body;
  }
}

function renderStressTests(scenarios) {
  const selectorContainer = document.getElementById('stress-scenario-selector');
  selectorContainer.innerHTML = '';

  scenarios.forEach((s, idx) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `stress-scenario-btn ${idx === 0 ? 'active' : ''}`;
    btn.textContent = s.name.split(' ')[0] + ' ' + (s.name.split(' ')[1] || '');
    btn.title = s.name;
    btn.addEventListener('click', () => {
      document.querySelectorAll('.stress-scenario-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      displayActiveScenario(s);
    });
    selectorContainer.appendChild(btn);
  });

  if (scenarios.length > 0) {
    displayActiveScenario(scenarios[0]);
  }
}

function displayActiveScenario(s) {
  document.getElementById('stress-scenario-name').textContent = s.name;
  document.getElementById('stress-scenario-desc').textContent = s.description;

  const cushionEl = document.getElementById('stress-cushion-badge');
  const deltaPct = (s.drawdown_delta * 100).toFixed(1);
  cushionEl.textContent = `${s.drawdown_delta >= 0 ? '+' : ''}${deltaPct}% Downside Cushion`;
  cushionEl.style.color = s.drawdown_delta >= 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)';
  cushionEl.style.borderColor = s.drawdown_delta >= 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)';

  document.getElementById('stress-curr-dd').textContent = `${(s.current_drawdown * 100).toFixed(1)}%`;
  document.getElementById('stress-curr-recovery').textContent = `Est. Recovery: ~${s.recovery_months} Months`;

  document.getElementById('stress-opt-dd').textContent = `${(s.optimal_drawdown * 100).toFixed(1)}%`;
  document.getElementById('stress-opt-recovery').textContent = `Est. Recovery: ~${s.optimal_recovery_months} Months`;

  document.getElementById('stress-worst-asset').textContent = s.worst_asset;
  document.getElementById('stress-best-asset').textContent = s.best_shelter;

  document.getElementById('stress-commentary-text').textContent = s.commentary;
}

function updateWhatIfCard(key) {
  const item = WHATIF_CATALOG[key];
  if (!item) return;

  document.getElementById('whatif-candidate-name').textContent = item.name;
  
  const sharpeEl = document.getElementById('whatif-sharpe-delta');
  sharpeEl.textContent = item.sharpeDelta;
  sharpeEl.className = `im-val ${item.positiveSharpe ? 'positive' : 'negative'}`;

  const volEl = document.getElementById('whatif-vol-delta');
  volEl.textContent = item.volDelta;
  volEl.className = `im-val ${item.positiveVol ? 'positive' : 'negative'}`;

  const enbEl = document.getElementById('whatif-enb-delta');
  enbEl.textContent = item.enbDelta;
  enbEl.className = 'im-val positive';

  document.getElementById('whatif-explanation-text').textContent = item.explanation;
}

function injectWhatIfAsset() {
  const item = WHATIF_CATALOG[activeWhatIfKey];
  if (!item) return;

  const rows = document.querySelectorAll('#asset-tbody tr');
  const existingTickers = Array.from(rows).map(r => r.querySelector('.ticker-name').textContent.trim());

  if (existingTickers.includes(item.ticker)) {
    alert(`${item.ticker} is already in your portfolio!`);
    return;
  }

  // Scale down existing weights to make room for new asset
  const newWeight = item.weight;
  const factor = (100 - newWeight) / 100.0;

  rows.forEach(r => {
    const input = r.querySelector('.weight-input');
    const oldVal = parseFloat(input.value) || 0;
    input.value = (oldVal * factor).toFixed(1);
  });

  addAssetRow(item.ticker, newWeight);
  updateWeightTotal();

  // Visual feedback
  const btn = document.getElementById('btn-inject-asset');
  const original = btn.innerHTML;
  btn.innerHTML = `<span>✓ Injected ${item.ticker}!</span>`;
  setTimeout(() => { btn.innerHTML = original; }, 2000);
}

function copyTradeTicket() {
  if (!currentPortfolioData) {
    alert('Please run the optimization engine first to generate your trade ticket.');
    return;
  }

  const actions = currentPortfolioData.rebalance_actions;
  const opt = currentPortfolioData.max_sharpe_portfolio;
  const curr = currentPortfolioData.current_portfolio;
  const sharpeDelta = (opt.sharpe_ratio - curr.sharpe_ratio).toFixed(2);

  const lines = [
    '========================================',
    'ALPHAWISE INSTITUTIONAL REBALANCE TICKET',
    `Timestamp: ${new Date().toISOString()}`,
    '========================================',
    `Optimal Sharpe: ${opt.sharpe_ratio.toFixed(2)} (${sharpeDelta >= 0 ? '+' : ''}${sharpeDelta} Δ)`,
    `Expected Volatility: ${(opt.volatility * 100).toFixed(1)}%`,
    '----------------------------------------',
    'ORDER EXECUTION INSTRUCTIONS:',
    '----------------------------------------'
  ];

  actions.forEach(a => {
    const deltaStr = (a.delta_weight * 100).toFixed(1);
    const targetStr = (a.target_weight * 100).toFixed(1);
    lines.push(`• ${a.action.padEnd(4)} ${a.ticker.padEnd(6)} | Target: ${targetStr.padStart(5)}% | Net: ${deltaStr >= 0 ? '+' : ''}${deltaStr}%`);
  });

  lines.push('========================================');
  lines.push('Fiduciary Fills Generated by Alphawise Engine');

  navigator.clipboard.writeText(lines.join('\n')).then(() => {
    const btn = document.getElementById('btn-copy-ticket');
    const orig = btn.innerHTML;
    btn.innerHTML = '<span>✓ Copied to Clipboard!</span>';
    setTimeout(() => { btn.innerHTML = orig; }, 2500);
  }).catch(() => {
    alert('Could not copy to clipboard. Please copy manually.');
  });
}

function renderRebalanceTable(actions) {
  const tbody = document.getElementById('rebalance-tbody');
  tbody.innerHTML = '';

  actions.forEach(item => {
    const tr = document.createElement('tr');
    const currPct = (item.current_weight * 100).toFixed(1);
    const targetPct = (item.target_weight * 100).toFixed(1);
    const deltaPct = (item.delta_weight * 100).toFixed(1);

    const actionClass = item.action.toLowerCase();

    tr.innerHTML = `
      <td><strong>${item.ticker}</strong></td>
      <td>${currPct}%</td>
      <td><strong style="color: var(--accent-blue);">${targetPct}%</strong></td>
      <td style="color: ${item.delta_weight > 0 ? 'var(--accent-emerald)' : item.delta_weight < 0 ? 'var(--accent-rose)' : 'var(--text-dim)'}; font-weight: 700;">
        ${item.delta_weight > 0 ? '+' : ''}${deltaPct}%
      </td>
      <td>
        <span class="action-pill ${actionClass}">${item.action}</span>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

/* =========================================================================
   AI Copilot Chat & Narrative Regeneration Handlers
   ========================================================================= */

let copilotHistory = [];

function setupCopilotEvents() {
  const launcher = document.getElementById('btn-open-copilot');
  const windowEl = document.getElementById('copilot-window');
  const closeBtn = document.getElementById('btn-close-copilot');
  const clearBtn = document.getElementById('btn-clear-chat');
  const form = document.getElementById('copilot-form');
  const input = document.getElementById('copilot-input');

  if (!launcher || !windowEl) return;

  launcher.addEventListener('click', () => {
    windowEl.classList.toggle('hidden');
    if (!windowEl.classList.contains('hidden')) {
      updateCopilotContextBadge();
      input.focus();
    }
  });

  closeBtn.addEventListener('click', () => {
    windowEl.classList.add('hidden');
  });

  clearBtn.addEventListener('click', () => {
    copilotHistory = [];
    const container = document.getElementById('copilot-messages');
    container.innerHTML = `
      <div class="chat-msg bot">
        <div class="msg-bubble">
          <p>🧹 <strong>Conversation reset.</strong></p>
          <p style="margin-top: 4px;">Ask me anything about your active portfolio allocations, risk metrics, or any stock market ticker.</p>
        </div>
      </div>
    `;
  });

  // Suggestion chips
  document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const prompt = chip.getAttribute('data-prompt');
      if (prompt) {
        input.value = prompt;
        submitCopilotMessage(prompt);
      }
    });
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (query) {
      submitCopilotMessage(query);
    }
  });
}

function updateCopilotContextBadge() {
  const badge = document.getElementById('copilot-context-label');
  if (!badge) return;
  if (currentPortfolioData && currentPortfolioData.metadata && currentPortfolioData.metadata.tickers) {
    const tickers = currentPortfolioData.metadata.tickers;
    const count = tickers.length;
    badge.textContent = `Portfolio Active: ${count} assets (${tickers.slice(0, 3).join(', ')}${count > 3 ? '...' : ''})`;
  } else {
    badge.textContent = 'Ready: Ask about your holdings or any stock ticker';
  }
}

function getActivePortfolioContext() {
  if (!currentPortfolioData) return null;
  const meta = currentPortfolioData.metadata || {};
  const curr = currentPortfolioData.current_portfolio || {};
  const opt = currentPortfolioData.max_sharpe_portfolio || {};
  const risk = currentPortfolioData.risk_metrics || {};
  const health = currentPortfolioData.health_score || {};
  const rebalance = currentPortfolioData.rebalance_actions || [];

  return {
    tickers: meta.tickers || [],
    curr_weights: curr.weights || {},
    opt_weights: opt.weights || {},
    curr_ret: curr.expected_return || 0,
    curr_vol: curr.volatility || 0,
    curr_sharpe: curr.sharpe_ratio || 0,
    opt_ret: opt.expected_return || 0,
    opt_vol: opt.volatility || 0,
    opt_sharpe: opt.sharpe_ratio || 0,
    effective_bets: risk.effective_bets || 0,
    health_score: health,
    rebalance_actions: rebalance.slice(0, 6),
    var_95: risk.var_95 || null,
    max_drawdown: risk.max_drawdown || null
  };
}

function formatMarkdown(text) {
  if (!text) return '';
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Italic
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Headers
  html = html.replace(/^### (.*$)/gim, '<h4 style="margin: 6px 0 2px; color: var(--accent-blue); font-size: 0.88rem;">$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3 style="margin: 8px 0 4px; color: var(--accent-blue); font-size: 0.95rem;">$1</h3>');
  // Bullet lists
  html = html.replace(/^\s*[-•]\s+(.*$)/gim, '<li style="margin-left: 14px; list-style-type: disc;">$1</li>');
  html = html.replace(/(<li.*<\/li>)/gms, '<ul style="padding-left: 6px; margin: 4px 0;">$1</ul>');
  // Paragraphs and breaks
  html = html.replace(/\n\n/g, '<p style="margin-top: 6px;"></p>');
  html = html.replace(/\n/g, '<br/>');
  return html;
}

async function submitCopilotMessage(userText) {
  const messagesContainer = document.getElementById('copilot-messages');
  const input = document.getElementById('copilot-input');
  const sendBtn = document.getElementById('btn-send-chat');

  // Append user bubble
  const userDiv = document.createElement('div');
  userDiv.className = 'chat-msg user';
  userDiv.innerHTML = `<div class="msg-bubble">${formatMarkdown(userText)}</div>`;
  messagesContainer.appendChild(userDiv);

  input.value = '';
  input.disabled = true;
  sendBtn.disabled = true;

  // Append thinking indicator
  const thinkingDiv = document.createElement('div');
  thinkingDiv.className = 'chat-msg bot thinking-msg';
  thinkingDiv.innerHTML = `
    <div class="msg-bubble">
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
      <span style="font-size: 0.72rem; color: var(--text-muted); margin-left: 8px;">Analyzing with Groq LPU...</span>
    </div>
  `;
  messagesContainer.appendChild(thinkingDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  try {
    const portfolioCtx = getActivePortfolioContext();
    const res = await ApiClient.sendChatMessage(userText, copilotHistory, portfolioCtx);

    // Save to history
    copilotHistory.push({ role: 'user', content: userText });
    copilotHistory.push({ role: 'assistant', content: res.reply });

    // Replace thinking indicator with response
    thinkingDiv.className = 'chat-msg bot';
    thinkingDiv.innerHTML = `<div class="msg-bubble">${formatMarkdown(res.reply)}</div>`;
  } catch (err) {
    thinkingDiv.className = 'chat-msg bot';
    thinkingDiv.innerHTML = `
      <div class="msg-bubble" style="border-color: var(--accent-rose); color: var(--accent-rose);">
        ⚠️ <strong>Error:</strong> ${err.message || 'Unable to connect to Copilot'}.
      </div>
    `;
  } finally {
    input.disabled = false;
    sendBtn.disabled = false;
    input.focus();
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
}

async function handleRegenerateAiMemo() {
  if (!currentPortfolioData) {
    alert('Please click "Run Quantitative Optimization" first to generate portfolio data.');
    return;
  }

  const btn = document.getElementById('btn-regen-ai');
  const textEl = document.getElementById('btn-regen-ai-text');
  btn.classList.add('loading');
  textEl.textContent = '⚡ Groq Thinking...';

  try {
    const ctx = getActivePortfolioContext();
    const res = await ApiClient.regenerateMemo('both', ctx);

    if (res.institutional_memo || res.roast_memo) {
      renderAiCommentary(res);
      textEl.textContent = '✓ AI Updated!';
    }
  } catch (err) {
    alert(`Could not regenerate memo: ${err.message}`);
    textEl.textContent = '⚡ AI Re-roll';
  } finally {
    setTimeout(() => {
      btn.classList.remove('loading');
      textEl.textContent = '⚡ AI Re-roll';
    }, 2200);
  }
}
