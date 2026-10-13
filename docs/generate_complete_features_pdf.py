import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 756, "ALPHAWISE TERMINAL v2.5 | EXHAUSTIVE FEATURE-BY-FEATURE DEMO SCRIPT")
            self.drawRightString(576, 756, "FULL TECHNICAL WALKTHROUGH")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, 750, 576, 750)
            
        # Footer
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 38, 576, 38)
        
        self.setFont("Helvetica", 8)
        self.drawString(36, 26, "Alphawise • Institutional Quantitative Portfolio & Risk Intelligence Platform")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 26, page_str)
        self.restoreState()

def build_complete_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=44,
        bottomMargin=44
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=3
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#0284C7'),
        spaceAfter=6
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#475569'),
        spaceAfter=8
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=8,
        spaceAfter=4
    )

    body_p = ParagraphStyle(
        'BodyP',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=11,
        textColor=colors.HexColor('#1E293B')
    )

    cue_p = ParagraphStyle(
        'CueP',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=11,
        textColor=colors.HexColor('#0284C7')
    )

    speech_p = ParagraphStyle(
        'SpeechP',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=11,
        textColor=colors.HexColor('#0F172A')
    )

    edge_p = ParagraphStyle(
        'EdgeP',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor('#059669') # Emerald edge
    )

    col_header = ParagraphStyle(
        'ColHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    story = []

    # Title Banner Block
    story.append(Paragraph("💎 Alphawise: Comprehensive Feature-by-Feature Demo Script", title_style))
    story.append(Paragraph("Exhaustive Screenplay Covering Every Specialty, Tab, Formula, and Engine Mechanism", subtitle_style))
    story.append(Paragraph("<b>Target Video Duration:</b> 6:30 – 7:30 Minutes &nbsp;|&nbsp; <b>Live App:</b> <code>http://localhost:3000</code> &nbsp;|&nbsp; <b>Presentation Target:</b> Technical Judges & Evaluators", meta_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=6))

    # Architecture & Feature Inventory Summary
    inv_data = [
        [
            Paragraph("<b>📋 COMPLETE FEATURE INVENTORY COVERED IN THIS SCRIPT:</b><br/>"
                      "<b>1. Top Header:</b> Branding, Dark/Light theme toggle, BlackRock Tear Sheet PDF export, Live backend heartbeat.<br/>"
                      "<b>2. Left Sidebar Universe Builder:</b> 4 Presets (Tech, 60/40, All-Weather, Inflation), Equal Weight, Clear All, Custom Ticker Add (+SPY, +QQQ, +NVDA, +GLD, +TLT, +BTC), dynamic weight inputs, 100% budget constraint validation meter, Lookback window (1Y–5Y), US 10Y Rf input, Max Allocation Cap bounds (25%–100%).<br/>"
                      "<b>3. Numerical Engine & Solver:</b> Charnes-Cooper hyperbolic transformation, SciPy SLSQP & CVXPY quadratic solvers, Ledoit-Wolf shrinkage, 4 Top Scorecards (Sharpe, Volatility, Return, Shannon Eigenvalue Effective Bets Neff).<br/>"
                      "<b>4. AI Diagnostic Hub:</b> 100-point Multi-Factor Health Score & 4 component breakdown bars, Dual-Voice Commentary (Institutional CIO Fiduciary Memo vs. 🌶️ FinTwit Roast), Groq Llama 3.3 70B AI Re-roll.<br/>"
                      "<b>5. 6 Tabbed Analytics Panes:</b> Efficient Frontier curve with custom markers, Macro Crisis Stress-Test (5 historical crashes with downside cushion & recovery months), What-If Sandbox (GLD, TLT, BTC, Cash injection with live Sharpe delta), Pearson Correlation Heatmap, Individual Asset Volatilities bar chart, 63-Day Rolling Stress Volatility time-series.<br/>"
                      "<b>6. Execution & Copilot:</b> Rebalance Trade Execution Ticket with trade deltas Δw, Copy to Clipboard, 1-click Apply Weights, Floating AI Copilot with real-time portfolio awareness & suggestion chips.", body_p)
        ]
    ]
    inv_table = Table(inv_data, colWidths=[540])
    inv_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(inv_table)
    story.append(Spacer(1, 8))

    def make_table(scenes):
        table_rows = [
            [
                Paragraph("<b>SCENE / TIMING</b>", col_header),
                Paragraph("<b>WHERE TO POINT & EXACT ACTION</b>", col_header),
                Paragraph("<b>WHAT TO SAY (SPOKEN SCRIPT & JUDGES EXPLANATION)</b>", col_header)
            ]
        ]
        for cue, visual, speech in scenes:
            table_rows.append([
                Paragraph(cue, cue_p),
                Paragraph(visual, body_p),
                Paragraph(speech, speech_p)
            ])
        t = Table(table_rows, colWidths=[85, 165, 290])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('TOPPADDING', (0,0), (-1,-1), 4.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4.5),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ]))
        return t

    # SECTION 1: HEADER & LIVE ENGINE
    story.append(Paragraph("1. Header Navigation, Theme Engine & Live Backend Health (0:00 – 0:40)", section_heading))
    s1 = [
        (
            "<b>0:00 - 0:20</b><br/>Terminal Identity<br/>& Problem Hook",
            "• Screen starts full browser at <code>http://localhost:3000</code>.<br/>"
            "• Point cursor to top logo: <code>Alphawise TERMINAL v2.5</code>.<br/>"
            "• Hover over the subtitle tag: <i>'Institutional Quantitative Engine & AI Portfolio Intelligence'</i>.",
            "\"Judges, modern wealth management tools suffer from a fatal flaw: they treat diversification as a nominal ticker count, while standard Markowitz optimization in practice acts as an 'error-maximizer' that produces unstable allocations.<br/><br/>"
            "This is <b>Alphawise Terminal v2.5</b>—an institutional platform combining Modern Portfolio Theory, spectral risk decomposition, historical crisis stress testing, and Groq-powered AI diagnostics into a unified financial terminal.\""
        ),
        (
            "<b>0:20 - 0:40</b><br/>Theme Switcher &<br/>Heartbeat Check",
            "• Point to the top-right <b>Live Status Badge</b>: pulsing green dot next to <code>Healthy: Alphawise Quantitative Engine</code>.<br/>"
            "• Click <b>🌙 Theme Toggle</b> (switches to crisp daylight mode, then back to dark terminal mode).",
            "\"Starting in the top header: Alphawise features an active health monitor polling our FastAPI backend at <code>/api/v1/health</code>, confirming real-time connectivity to our numerical engine.<br/><br/>"
            "Next to it is our persistent Theme Engine: one click toggles between institutional dark mode and high-contrast day mode, with zero layout flash or style lag.\""
        )
    ]
    story.append(make_table(s1))
    story.append(Spacer(1, 8))

    # SECTION 2: SIDEBAR CONTROLS
    story.append(Paragraph("2. Portfolio Universe Builder, Presets & Constraints (0:40 – 1:45)", section_heading))
    s2 = [
        (
            "<b>0:40 - 1:05</b><br/>Module 1: Strategy Presets & Quick Utils",
            "• Move cursor to <b>Portfolio Presets</b> in the sidebar.<br/>"
            "• Point out the 4 presets: <code>🔥 Tech Megacaps</code>, <code>⚖️ Classic 60/40</code>, <code>🛡️ All-Weather</code>, <code>⚡ Inflation Shield</code>.<br/>"
            "• Click <code>🔥 Tech Megacaps</code>.<br/>"
            "• Point to <code>⚖️ Equal Weight</code> and <code>🧹 Clear All</code> utility buttons.",
            "\"In the left control panel, Module 1 provides one-click institutional templates:<br/>"
            "• <b>Tech Megacaps</b> (AAPL, MSFT, NVDA, GOOGL, AMZN)<br/>"
            "• <b>Classic 60/40</b> (Equities and Treasuries)<br/>"
            "• <b>All-Weather</b> (Risk parity across bonds, commodities, and equities)<br/>"
            "• <b>Inflation Shield</b> (TIPS, Energy, Gold).<br/><br/>"
            "Let's select Tech Megacaps. Notice our quick utility buttons: <b>Equal Weight</b> rebalances any portfolio uniformly, while <b>Clear All</b> resets the canvas instantaneously.\""
        ),
        (
            "<b>1:05 - 1:25</b><br/>Module 2: Ticker Add & Allocation Meter",
            "• Point to Add Asset bar.<br/>"
            "• Click Quick Add chips: <code>+GLD</code> (Gold) and <code>+TLT</code> (Treasuries).<br/>"
            "• Point to holdings table rows (editable weight % inputs & delete buttons).<br/>"
            "• Point to <b>Allocation Meter</b>: green track reading <b>100.0% Balanced</b>.",
            "\"In Module 2, users can add any stock, ETF, or crypto ticker. We also provide Quick-Add chips for standard hedging assets: let's click <b>+GLD</b> and <b>+TLT</b>.<br/><br/>"
            "Each asset features inline editable target weights. Crucially, look at the <b>Allocation Meter</b>: it enforces an exact budget constraint (sum w_i = 100%). If weights diverge from 100%, the bar turns amber or red and disables execution, guaranteeing mathematical consistency.\""
        ),
        (
            "<b>1:25 - 1:45</b><br/>Module 3: Quantitative Parameters",
            "• Scroll down sidebar to Module 3.<br/>"
            "• Point to <b>Historical Lookback Window</b> (1Y, 2Y, 3Y, 5Y).<br/>"
            "• Point to <b>Risk-Free Rate (Rf)</b> (set to 4.5%).<br/>"
            "• Point to <b>Max Allocation Cap</b> (No Cap, 50%, 40%, 30%, 25%).",
            "\"Module 3 controls the mathematical bounds of our optimizer:<br/>"
            "1. <b>Lookback Window:</b> Selects the historical return sampling period (1 to 5 years).<br/>"
            "2. <b>Risk-Free Rate:</b> Set to the US 10-Year Treasury benchmark (4.5%) to anchor the Sharpe denominator.<br/>"
            "3. <b>Max Allocation Cap:</b> This introduces inequality box constraints (w_i <= w_max), preventing the solver from creating extreme, un-investable corner portfolios in a single asset.\""
        )
    ]
    story.append(make_table(s2))
    story.append(Spacer(1, 8))

    # Page Break
    story.append(PageBreak())

    # SECTION 3: METRICS & SPECTRAL DECOMPOSITION
    story.append(Paragraph("3. Optimization Execution & Top Performance Scorecards (1:45 – 2:40)", section_heading))
    s3 = [
        (
            "<b>1:45 - 2:10</b><br/>Optimizer Execution & Metric Cards 1 & 2",
            "• Click <code>⚡ Run Institutional Optimization</code>.<br/>"
            "• Highlight the ~800ms solver execution.<br/>"
            "• Point to <b>Card 1: Optimal Sharpe Ratio</b> (green delta badge).<br/>"
            "• Point to <b>Card 2: Annualized Volatility (σp)</b>.",
            "\"Now, let's execute our solver.<br/><br/>"
            "Alphawise runs the Charnes-Cooper hyperbolic transformation to convert the non-linear Maximum Sharpe problem into a convex quadratic program solved via SciPy SLSQP and CVXPY.<br/><br/>"
            "In Card 1, see the <b>Optimal Sharpe Ratio</b>: it highlights the exact delta improvement over the user's current baseline.<br/><br/>"
            "Card 2 displays the portfolio's <b>Annualized Volatility (σp = sqrt(w^T Σ w))</b>, factoring in the full 252-day covariance structure.\""
        ),
        (
            "<b>2:10 - 2:40</b><br/>Card 3 & Card 4: Spectral Bets (N_eff)",
            "• Point to <b>Card 3: Expected Return (μp)</b>.<br/>"
            "• Point to <b>Card 4: Effective Bets (N_eff)</b> and hover over <code>INFO ⓘ</code>.",
            "\"Card 3 displays the annualized compounded return.<br/><br/>"
            "Now examine our fourth card: <b>Effective Number of Bets (N_eff)</b>. This is a signature quantitative feature.<br/><br/>"
            "Standard brokers claim that owning 7 stocks gives you 7 bets. Alphawise performs a full spectral decomposition of the Pearson correlation matrix (C = V Λ V^T) and computes the Shannon entropy of normalized eigenvalues: N_eff = exp(-Σ p_k ln p_k).<br/><br/>"
            "This mathematically proves that our 7 tech and growth holdings only yield ~2.7 truly independent risk factors. We replace nominal diversification with orthogonal factor exposure.\""
        )
    ]
    story.append(make_table(s3))
    story.append(Spacer(1, 8))

    # SECTION 4: AI CIO DIAGNOSTIC HUB
    story.append(Paragraph("4. AI CIO Diagnostic Hub: Health Score & Dual Commentary (2:40 – 3:45)", section_heading))
    s4 = [
        (
            "<b>2:40 - 3:15</b><br/>Health Score & 4 Factor Breakdown Bars",
            "• Scroll to <b>Section 2: AI Diagnostic Hub</b>.<br/>"
            "• Point to the large <b>Health Score (e.g. 84/100)</b> and grade badge.<br/>"
            "• Trace the 4 sub-metric progress tracks:<br/>"
            "1. Diversification<br/>2. Sharpe Efficiency<br/>3. Volatility Drag<br/>4. Tail Resilience.",
            "\"Section 2 is our <b>AI Portfolio Diagnostic Hub</b>.<br/><br/>"
            "At the top is our composite 100-point Health Score, synthesized across 4 quantitative pillars:<br/>"
            "1. <b>Diversification:</b> Evaluates our spectral N_eff against nominal asset count.<br/>"
            "2. <b>Sharpe Efficiency:</b> Current Sharpe relative to the theoretical tangency frontier.<br/>"
            "3. <b>Volatility Drag:</b> Penalizes excessive variance compounding drag.<br/>"
            "4. <b>Tail Resilience:</b> Evaluates 95% Cornish-Fisher Value-at-Risk accounting for skewness and kurtosis.\""
        ),
        (
            "<b>3:15 - 3:45</b><br/>Institutional Memo vs. 🌶️ Roast & AI Re-roll",
            "• Point to <b>Executive Fiduciary Summary</b> and Callout Cards in Institutional Memo.<br/>"
            "• Click <code>🌶️ Roast My Portfolio</code> button.<br/>"
            "• Highlight the flaming pill: <code>🌶️ Extreme Roast</code> & read the punchline.<br/>"
            "• Point to <code>⚡ AI Re-roll</code> button.",
            "\"Alphawise bridges complex math to human understanding through dual-persona AI powered by Groq Llama 3.3 70B.<br/><br/>"
            "In <b>Institutional Memo</b> mode, the AI writes a fiduciary investment teardown analyzing factor orthogonality, tail risks, and rebalance theses.<br/><br/>"
            "Click <b>Roast My Portfolio</b>, and the persona shifts to a sharp, satirical FinTwit breakdown—humorously tearing down retail biases and hype-chasing in viral language.<br/><br/>"
            "Users can click <b>AI Re-roll</b> to query the Groq LLM endpoint dynamically for fresh perspectives.\""
        )
    ]
    story.append(make_table(s4))
    story.append(Spacer(1, 8))

    # Page Break
    story.append(PageBreak())

    # SECTION 5: 6 INTERACTIVE CHARTS & VISUALIZATIONS
    story.append(Paragraph("5. Interactive Visual Analytics & Crisis Stress-Testing (3:45 – 5:15)", section_heading))
    s5 = [
        (
            "<b>3:45 - 4:10</b><br/>Tab 1: Efficient Frontier Visualization",
            "• Scroll to <b>Section 3: Tabbed Visualizations</b>.<br/>"
            "• Click Tab 1: <code>📈 Efficient Frontier</code>.<br/>"
            "• Hover cursor over:<br/>"
            "- Frontier curve (scatter line)<br/>"
            "- Green star: Tangency Max Sharpe<br/>"
            "- Blue triangle: Min Volatility<br/>"
            "- Red diamond: Current Portfolio<br/>"
            "- Gray circles: Individual assets.",
            "\"Section 3 provides 6 deep quantitative visualization panes.<br/><br/>"
            "Pane 1 renders the <b>Efficient Frontier</b>. We compute and plot the parametric Markowitz hyperbola.<br/><br/>"
            "Notice our visual anchors:<br/>"
            "• <b>Green Star:</b> The Tangency Portfolio maximizing the Sharpe angle from Rf.<br/>"
            "• <b>Blue Triangle:</b> Global Minimum Variance portfolio.<br/>"
            "• <b>Red Diamond:</b> The user's current baseline.<br/>"
            "• <b>Gray Points:</b> Individual asset coordinates showing their standalone risk-return profiles.\""
        ),
        (
            "<b>4:10 - 4:35</b><br/>Tab 2: Macro Crisis Stress-Test Simulator",
            "• Click Tab 2: <code>💥 Macro Crisis Stress-Test</code>.<br/>"
            "• Click scenario selector pills:<br/>"
            "1. <b>2020 COVID Shock</b><br/>2. <b>2022 Rate Hike</b><br/>3. <b>2008 GFC</b><br/>4. <b>1970s Stagflation</b>.<br/>"
            "• Point to <b>Downside Cushion Badge (+8.4%)</b>, Drawdown comparison boxes, and worst/best asset highlights.",
            "\"Pane 2 is our <b>Historical Crisis Stress-Test Simulator</b>.<br/><br/>"
            "Static variance assumes normal Gaussian returns. We stress-test the user's exact asset weights against 5 historical macro shocks: 2020 COVID, 2022 Fed rate tightening, 2008 Lehman collapse, and 1970s stagflation.<br/><br/>"
            "Alphawise calculates drawdown comparisons in real time: showing our optimized portfolio provides an <b>8.4% downside capital cushion</b>, halves estimated recovery time, and highlights the worst-hit asset versus the best safe haven.\""
        ),
        (
            "<b>4:35 - 4:55</b><br/>Tab 3: Interactive What-If Sandbox",
            "• Click Tab 3: <code>🎛️ What-If Sandbox</code>.<br/>"
            "• Click test injection pills:<br/>"
            "<code>+ 10% Gold (GLD)</code>, <code>+ 15% Long Treasuries (TLT)</code>.<br/>"
            "• Point to projected metrics: Sharpe Delta (+0.14), Volatility Delta (-1.8%), Bets Improvement (+0.7).<br/>"
            "• Point to <code>⚡ Inject into Portfolio Table</code> button.",
            "\"Pane 3 is our <b>Interactive What-If Sandbox</b>.<br/><br/>"
            "Before reallocating capital, risk managers can simulate injecting orthogonal asset classes like physical gold, long-term bonds, or Bitcoin.<br/><br/>"
            "It computes the marginal Sharpe delta, volatility reduction, and effective bets improvement in real time, and allows users to click <b>Inject into Portfolio Table</b> to apply it with zero friction.\""
        ),
        (
            "<b>4:55 - 5:15</b><br/>Tabs 4, 5 & 6: Heatmap, Bar Chart & Rolling Vol",
            "• Click Tab 4: <code>🗺️ Correlation Matrix</code> (point to colors).<br/>"
            "• Click Tab 5: <code>📊 Asset Volatilities</code> (point to bar comparisons).<br/>"
            "• Click Tab 6: <code>📉 Rolling Stress Volatility</code> (point to 63-day time-series).",
            "\"Pane 4 displays the interactive Pearson Correlation Heatmap: identity diagonal in acid green, high collinearity in coral, and negative correlation shelters in emerald.<br/><br/>"
            "Pane 5 compares individual asset volatilities against portfolio-level risk.<br/><br/>"
            "Pane 6 plots <b>63-Day Rolling Realized Volatility</b> over historical trading days, proving that our optimized tangency portfolio consistently dampens volatility spikes during market turbulence.\""
        )
    ]
    story.append(make_table(s5))
    story.append(Spacer(1, 8))

    # Page Break
    story.append(PageBreak())

    # SECTION 6: EXECUTION TICKET, COPILOT & TEAR SHEET
    story.append(Paragraph("6. Trade Execution Ticket, AI Copilot & Tear Sheet Export (5:15 – 6:30)", section_heading))
    s6 = [
        (
            "<b>5:15 - 5:40</b><br/>Rebalancing Ticket & 1-Click Execution",
            "• Scroll to <b>Section 4: Rebalancing Table</b>.<br/>"
            "• Trace table headers: Asset, Current %, Optimized %, Delta (Δw), Action (BUY/SELL/HOLD).<br/>"
            "• Point to <code>📋 Copy Trade Ticket</code>.<br/>"
            "• Point to <code>⚡ Apply Optimized Weights</code>.",
            "\"In Section 4, Alphawise converts quantitative optimization into concrete trading orders.<br/><br/>"
            "Our <b>Rebalance Ticket</b> calculates the exact weight delta (Δw) for each security with explicit BUY, SELL, or TRIM actions.<br/><br/>"
            "Users can click <b>Copy Trade Ticket</b> to copy broker-ready limit/market instructions to their clipboard, or click <b>Apply Optimized Weights</b> to overwrite the active universe parameters in one click.\""
        ),
        (
            "<b>5:40 - 6:05</b><br/>Floating AI Copilot & State Awareness",
            "• Click the floating button in bottom right:<br/>"
            "<code>🤖 Ask Copilot</code>.<br/>"
            "• Show the slide-out drawer.<br/>"
            "• Point to the green active context label.<br/>"
            "• Click suggestion pill: <i>'Why buy/sell these?'</i>.<br/>"
            "• Show response streaming in.",
            "\"In the bottom right corner is our floating <b>AI Copilot</b>.<br/><br/>"
            "The Copilot is state-aware: it continuously receives the full portfolio covariance matrix, current holdings, and trade deltas via structured prompt injection.<br/><br/>"
            "Users can click pre-built prompt pills or type questions like <i>'Why are you recommending these trades?'</i> or <i>'Check valuation for NVDA'</i>, receiving instant, contextually accurate answers without leaving the dashboard.\""
        ),
        (
            "<b>6:05 - 6:30</b><br/>BlackRock Tear Sheet & Final Pitch",
            "• Scroll to the top header.<br/>"
            "• Click <code>📄 Export Tear Sheet</code> button.<br/>"
            "• Look directly into camera for concluding statement.",
            "\"Finally, by clicking <b>Export Tear Sheet</b> in the header, Alphawise triggers an institutional, BlackRock-grade print layout compiling executive metrics, holdings, and risk disclaimers into a client-ready document.<br/><br/>"
            "To conclude: Alphawise delivers end-to-end portfolio intelligence—from spectral math and convex solvers to stress testing, AI commentary, and seamless trade execution.<br/><br/>"
            "Thank you, judges. We are now ready for your questions!\""
        )
    ]
    story.append(make_table(s6))
    story.append(Spacer(1, 10))

    # TECHNICAL ARCHITECTURE CHEAT SHEET FOR JUDGES Q&A
    story.append(Paragraph("📐 Technical Architecture & Math Reference for Judges' Q&A", section_heading))
    ref_data = [
        [
            Paragraph("<b>• Mathematical Formulation:</b><br/>"
                      "Max Sharpe Tangency Problem: min_w - (w^T μ - Rf) / sqrt(w^T Σ w) subject to Σ w_i = 1 and 0 <= w_i <= w_max.<br/>"
                      "Solved via Charnes-Cooper variable substitution y = w / (w^T μ - Rf) yielding a quadratic programming problem.<br/><br/>"
                      "<b>• Spectral Shannon Entropy:</b><br/>"
                      "Eigenvalues λ_1...λ_N of correlation matrix C. Normalized weights p_k = λ_k / N. Neff = exp(-Σ p_k ln p_k).<br/><br/>"
                      "<b>• Robustness to Overfitting:</b><br/>"
                      "Ledoit-Wolf shrinkage towards constant correlation matrix reduces estimation variance when T is small relative to N.<br/><br/>"
                      "<b>• Tech Stack & Performance:</b><br/>"
                      "FastAPI (Python 3.11), NumPy, Pandas, SciPy, CVXPY, Chart.js, Groq Llama 3.3 70B (sub-second generation).", body_p)
        ]
    ]
    ref_table = Table(ref_data, colWidths=[540])
    ref_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#94A3B8')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(ref_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Complete features PDF generated successfully at: {filename}")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "Alphawise_Complete_Features_Demo_Script.pdf"
    build_complete_pdf(out_file)
