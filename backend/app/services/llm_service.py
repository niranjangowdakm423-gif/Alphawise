"""
Alphawise LLM Service — Groq & OpenAI-Compatible Inference Layer
================================================================
Provides high-speed quantitative narrative generation and interactive
portfolio/stock chatbot assistance using Groq (Llama 3.3 70B / 3.1 8B)
or any OpenAI-compatible API (including Ollama).

Features:
  1. Dynamic Institutional CIO Investment Memo generation
  2. Spicy FinTwit / WallStreetBets Portfolio Roast generation
  3. Interactive Copilot: answers portfolio allocation questions
     and normal stock market queries with live yfinance real-time context.
  4. Non-blocking graceful fallback: if API key is missing or endpoint
     fails, callers fall back to deterministic analytics.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
import yfinance as yf

from app.core.config import settings

logger = logging.getLogger("alphawise.llm")


class LLMService:
    """Async client for Groq / OpenAI-compatible LLM endpoints."""

    @classmethod
    def is_configured(cls) -> bool:
        """Returns True if an API key or local LLM base URL is configured."""
        if settings.active_api_key:
            return True
        # If pointing to local Ollama (which does not require a key)
        if "localhost" in settings.active_base_url or "127.0.0.1" in settings.active_base_url:
            return True
        return False

    @classmethod
    async def chat_completion(
        cls,
        messages: List[Dict[str, str]],
        temperature: float = 0.6,
        max_tokens: int = 1000,
        response_format: Optional[Dict[str, str]] = None,
        timeout: float = 12.0,
    ) -> Optional[str]:
        """
        Executes an async chat completion against the configured LLM endpoint.
        Returns the raw message content string, or None upon error.
        """
        if not cls.is_configured():
            logger.info("LLM service not configured (missing GROQ_API_KEY). Using fallback.")
            return None

        headers = {"Content-Type": "application/json"}
        if settings.active_api_key:
            headers["Authorization"] = f"Bearer {settings.active_api_key}"

        payload: Dict[str, Any] = {
            "model": settings.active_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        endpoint = f"{settings.active_base_url.rstrip('/')}/chat/completions"

        # Candidate models to try in order of preference
        primary = settings.active_model
        candidate_models = [primary]
        for fallback_m in ["llama-3.1-8b-instant", "llama3-8b-8192", "llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"]:
            if fallback_m not in candidate_models:
                candidate_models.append(fallback_m)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                for model_name in candidate_models:
                    payload: Dict[str, Any] = {
                        "model": model_name,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                    if response_format:
                        payload["response_format"] = response_format

                    resp = await client.post(endpoint, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            return choices[0]["message"]["content"]
                    else:
                        logger.warning(
                            "LLM endpoint %s model '%s' returned status %d: %s",
                            endpoint,
                            model_name,
                            resp.status_code,
                            resp.text[:200],
                        )
                        # If unauthorized (401), invalid API key — trying other models won't help
                        if resp.status_code == 401:
                            return None
                        # For other errors (like 400 Bad Request / Invalid Model), loop and try next model
        except httpx.TimeoutException:
            logger.warning("LLM request timed out after %.1fs. Falling back.", timeout)
        except Exception as exc:
            logger.warning("LLM call failed (%s). Falling back.", exc)

        return None

    # =========================================================================
    # 1. Dynamic Institutional CIO Memo
    # =========================================================================

    @classmethod
    async def generate_institutional_memo(
        cls,
        tickers: List[str],
        curr_weights: Dict[str, float],
        opt_weights: Dict[str, float],
        curr_ret: float,
        curr_vol: float,
        curr_sharpe: float,
        opt_ret: float,
        opt_vol: float,
        opt_sharpe: float,
        effective_bets: float,
        health_score: Dict[str, Any],
        rebalance_actions: List[Dict[str, Any]],
        stress_tests: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Prompts Groq Llama 3.3 to produce a high-pedigree fiduciary memo.
        """
        system_prompt = (
            "You are a Chief Investment Officer and Chief Risk Officer at a Tier-1 institutional quantitative asset manager.\n"
            "Analyze the quantitative portfolio optimization data and produce an executive-ready Fiduciary Risk & Allocation Memo.\n"
            "Write with precise financial vocabulary (eigenvalue dispersion, tangency ray, factor crowding, Cornish-Fisher tail risk).\n"
            "You must return pure JSON matching this exact schema:\n"
            "{\n"
            '  "title": "Institutional Fiduciary Risk & Allocation Memo",\n'
            '  "health_grade": "A|B|C|D|F",\n'
            '  "health_rating": "<short institutional rating>",\n'
            '  "executive_summary": "<2-3 concise sentences detailing return, vol, and Sharpe gain>",\n'
            '  "diversification_analysis": "<analysis of spectral effective bets and correlation crowding>",\n'
            '  "risk_tail_warning": "<warning regarding simulated macro drawdowns and concentrated risk>",\n'
            '  "rebalance_rationale": "<actionable reallocation thesis explaining top buy/sell trades>"\n'
            "}"
        )

        user_content = json.dumps({
            "tickers": tickers,
            "current_weights": curr_weights,
            "optimal_tangency_weights": opt_weights,
            "current_performance": {
                "annualized_return": f"{curr_ret * 100:.2f}%",
                "annualized_volatility": f"{curr_vol * 100:.2f}%",
                "sharpe_ratio": round(curr_sharpe, 3),
            },
            "optimal_performance": {
                "annualized_return": f"{opt_ret * 100:.2f}%",
                "annualized_volatility": f"{opt_vol * 100:.2f}%",
                "sharpe_ratio": round(opt_sharpe, 3),
            },
            "effective_number_of_bets": round(effective_bets, 2),
            "total_assets": len(tickers),
            "health_grade": health_score.get("grade", "B"),
            "health_score": health_score.get("score", 70),
            "rebalance_actions": rebalance_actions[:5],
            "stress_tests": [
                {"name": s.get("name"), "curr_drawdown": f"{s.get('current_drawdown', 0)*100:.1f}%"}
                for s in stress_tests[:3]
            ],
        })

        raw = await cls.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
            timeout=10.0,
        )

        if not raw:
            return None

        try:
            parsed = json.loads(raw)
            required_keys = [
                "title", "health_grade", "health_rating",
                "executive_summary", "diversification_analysis",
                "risk_tail_warning", "rebalance_rationale",
            ]
            if all(k in parsed for k in required_keys):
                return parsed
        except Exception as err:
            logger.warning("Failed to parse LLM institutional memo JSON: %s", err)

        return None

    # =========================================================================
    # 2. Dynamic WallStreetBets / FinTwit Roast
    # =========================================================================

    @classmethod
    async def generate_roast_memo(
        cls,
        tickers: List[str],
        curr_weights: Dict[str, float],
        opt_weights: Dict[str, float],
        curr_ret: float,
        curr_vol: float,
        curr_sharpe: float,
        opt_sharpe: float,
        effective_bets: float,
        rebalance_actions: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Prompts Groq Llama 3.3 to mercilessly roast the user's asset allocation.
        """
        system_prompt = (
            "You are an unhinged, hilariously sarcastic WallStreetBets / FinTwit degen roast master.\n"
            "Your mission: roast the user's investment portfolio allocations with ruthless financial humor.\n"
            "Call out their tech bagholding, fake diversification (owning 5 mega-cap tech stocks and thinking they're safe), "
            "boomer bond holdings losing to inflation, or weird meme bets.\n"
            "Use internet finance slang appropriately (Wendy's dumpster, diamond hands, Jensen Huang, money printer, boomer beta).\n"
            "You must return pure JSON with this exact schema:\n"
            "{\n"
            '  "title": "WallStreetBets / FinTwit Teardown",\n'
            '  "headline": "<spicy punchy sarcastic headline in quotes>",\n'
            '  "roast_body": "<a sharp, funny, savage 3-paragraph roast tearing their weights and bets apart>",\n'
            '  "verdict": "Verdict: <actionable sarcastic bottom line>",\n'
            '  "spicy_rating": "🌶️🌶️🌶️ Extreme Roast | 🌶️🌶️ High Heat | 🌶️ Mildly Roasted"\n'
            "}"
        )

        user_content = json.dumps({
            "holdings": curr_weights,
            "current_sharpe": round(curr_sharpe, 2),
            "optimal_sharpe": round(opt_sharpe, 2),
            "effective_bets": f"{effective_bets:.2f} out of {len(tickers)} tickers",
            "volatility": f"{curr_vol * 100:.1f}%",
            "suggested_trades": [
                f"{a['action']} {a['ticker']} ({a['delta_weight']*100:+.1f}%)"
                for a in rebalance_actions[:4]
            ],
        })

        raw = await cls.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.85,
            response_format={"type": "json_object"},
            timeout=10.0,
        )

        if not raw:
            return None

        try:
            parsed = json.loads(raw)
            required_keys = ["title", "headline", "roast_body", "verdict", "spicy_rating"]
            if all(k in parsed for k in required_keys):
                return parsed
        except Exception as err:
            logger.warning("Failed to parse LLM roast memo JSON: %s", err)

        return None

    # =========================================================================
    # 3. Interactive Copilot: Stock & Portfolio Chat
    # =========================================================================

    @classmethod
    def _extract_tickers(cls, query: str) -> List[str]:
        """Finds likely stock ticker symbols mentioned in the query."""
        # Match $TICKER or standalone uppercase 1-5 letters
        found = set(re.findall(r"\$([A-Za-z]{1,5})", query))
        # Look for common ticker words
        words = re.findall(r"\b[A-Z]{2,5}\b", query)
        common_words = {"AND", "THE", "WHY", "HOW", "WHAT", "WHO", "CAN", "FOR", "BUY", "SELL", "HOLD", "ANY", "WITH"}
        for w in words:
            if w not in common_words:
                found.add(w)
        return list(found)[:3]

    @classmethod
    def fetch_live_stock_info(cls, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetches lightweight real-time data using yfinance for ground truth."""
        try:
            t = yf.Ticker(ticker)
            fast = getattr(t, "fast_info", None)
            if fast and hasattr(fast, "last_price") and fast.last_price is not None:
                price = float(fast.last_price)
                prev_close = float(getattr(fast, "previous_close", price))
                change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else 0.0
                return {
                    "ticker": ticker.upper(),
                    "price": round(price, 2),
                    "change_pct": round(change_pct, 2),
                    "currency": getattr(fast, "currency", "USD"),
                    "market_cap": getattr(fast, "market_cap", None),
                    "year_high": round(float(getattr(fast, "year_high", 0.0)), 2),
                    "year_low": round(float(getattr(fast, "year_low", 0.0)), 2),
                }
            # Fallback to info dict
            info = t.info
            if info and "currentPrice" in info or "regularMarketPrice" in info:
                price = info.get("currentPrice") or info.get("regularMarketPrice")
                return {
                    "ticker": ticker.upper(),
                    "name": info.get("shortName", ticker),
                    "price": price,
                    "change_pct": info.get("regularMarketChangePercent", 0.0),
                    "sector": info.get("sector", "N/A"),
                    "pe_ratio": info.get("trailingPE"),
                    "summary": info.get("longBusinessSummary", "")[:300],
                }
        except Exception as exc:
            logger.debug("yfinance lookup for %s failed: %s", ticker, exc)
        return None

    @classmethod
    async def chat_copilot(
        cls,
        message: str,
        conversation_history: List[Dict[str, str]],
        portfolio_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Interactive chatbot co-pilot that answers based on:
          1. Invested portfolio holdings, weights, risk metrics, and rebalances.
          2. Normal stock market queries (P/E, company summaries, live price checks).
        """
        # 1. Detect if any ticker is referenced
        mentioned_tickers = cls._extract_tickers(message)
        stock_live_data = {}
        for t in mentioned_tickers:
            live = cls.fetch_live_stock_info(t)
            if live:
                stock_live_data[t] = live

        # 2. Build system prompt
        system_prompt = (
            "You are Alphawise Copilot — an institutional-grade quantitative portfolio manager "
            "and expert financial analyst.\n\n"
            "You serve two primary functions:\n"
            "1. INVESTED PORTFOLIO ADVISOR: When the user asks about their portfolio, holdings, "
            "risk, Sharpe ratio, Effective Number of Bets (N_eff), stress tests, or rebalancing, "
            "you reference their EXACT active portfolio data provided below.\n"
            "2. GENERAL STOCK & MARKET EXPERT: When the user asks about a general stock, company fundamentals, "
            "valuation, financial concepts, or market dynamics, you provide clear, sharp, institutional-grade insights.\n\n"
            "Guidelines:\n"
            "- Be concise, direct, and actionable.\n"
            "- If live price or valuation data is available in the context, quote it directly.\n"
            "- For questions asking why certain stocks should be bought or sold, explain the mathematical rationale "
            "(risk contribution, volatility reduction, tangency Sharpe optimization).\n"
            "- Always format numbers cleanly (percentages with %, dollars with $).\n"
            "- Include a brief fiduciary disclaimer when giving allocation suggestions."
        )

        context_blocks = []
        if portfolio_context:
            context_blocks.append(
                f"### ACTIVE INVESTED PORTFOLIO CONTEXT:\n{json.dumps(portfolio_context, indent=2)}"
            )

        if stock_live_data:
            context_blocks.append(
                f"### LIVE MARKET DATA (yfinance):\n{json.dumps(stock_live_data, indent=2)}"
            )

        full_system_content = system_prompt
        if context_blocks:
            full_system_content += "\n\n" + "\n\n".join(context_blocks)

        messages = [{"role": "system", "content": full_system_content}]
        # Append recent history (up to last 6 turns to manage context)
        for h in conversation_history[-6:]:
            if "role" in h and "content" in h:
                messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": message})

        # 3. Call LLM
        reply = await cls.chat_completion(
            messages=messages,
            temperature=0.6,
            max_tokens=800,
            timeout=12.0,
        )

        if not reply:
            logger.info("Using intelligent copilot fallback engine")
            reply = cls._generate_copilot_fallback(
                message=message,
                portfolio_context=portfolio_context,
                stock_live_data=stock_live_data,
            )

        return {
            "reply": reply,
            "mentioned_tickers": list(stock_live_data.keys()),
            "live_data": stock_live_data,
            "model": settings.active_model if (reply and cls.is_configured()) else "alphawise-quant-engine",
        }

    @classmethod
    def _generate_copilot_fallback(
        cls,
        message: str,
        portfolio_context: Optional[Dict[str, Any]],
        stock_live_data: Dict[str, Any],
    ) -> str:
        msg = message.strip().lower()

        # 1. Greetings
        if re.search(r"\b(hi|hello|hey|greetings|howdy|sup|good morning|good evening)\b", msg):
            ctx_summary = ""
            if portfolio_context and "tickers" in portfolio_context:
                tickers = portfolio_context.get("tickers", [])
                ctx_summary = f" I am actively monitoring your portfolio universe of **{len(tickers)} assets** ({', '.join(tickers)})."
            return (
                f"👋 **Hello! Welcome to Alphawise Copilot.**{ctx_summary}\n\n"
                "I have real-time mathematical awareness of your portfolio holdings and live market data. You can ask me:\n"
                "• *'Why should I buy or sell these specific assets?'*\n"
                "• *'What is my biggest portfolio risk and how do I fix it?'*\n"
                "• *'Explain my Effective Number of Bets (N_eff)'*\n"
                "• Or ask for real-time fundamental analytics on any ticker (e.g. *'Check NVDA'* or *'P/E of AAPL'*)."
            )

        # 2. Rebalancing / Why buy or sell
        if any(w in msg for w in ["why", "buy", "sell", "rebalance", "trim", "trade"]):
            if portfolio_context and "rebalance_actions" in portfolio_context:
                actions = portfolio_context.get("rebalance_actions", [])
                curr_sharpe = portfolio_context.get("curr_sharpe", "N/A")
                opt_sharpe = portfolio_context.get("opt_sharpe", "N/A")
                action_lines = []
                for a in actions[:5]:
                    ticker = a.get("ticker", "")
                    act = a.get("action", "")
                    diff = a.get("diff_pct", 0)
                    action_lines.append(f"• **{act} {ticker}** ({diff:+.1f}%): Aligns position with optimal tangency weights.")
                action_text = "\n".join(action_lines) if action_lines else "• Rebalance positions toward tangency weights."
                return (
                    f"📊 **Rebalancing Rationale (Markowitz Tangency Solver):**\n\n"
                    f"The quantitative solver moves your portfolio from a Sharpe ratio of **{curr_sharpe}** to **{opt_sharpe}** along the Efficient Frontier.\n\n"
                    f"**Key Trade Directives:**\n{action_text}\n\n"
                    "**Mathematical Thesis:** By trimming over-concentrated equity momentum and rotating capital into orthogonal hedges, you minimize portfolio variance (wᵀΣw) per unit of expected return."
                )
            return (
                "📊 **Rebalancing Optimization Thesis:**\n\n"
                "The optimizer adjusts weights to maximize the portfolio Sharpe ratio (Charnes-Cooper Tangency Solver). "
                "Assets with high covariance collinearity are trimmed, while assets offering diversification benefit are allocated more weight to reach the optimal point on the Efficient Frontier."
            )

        # 3. Biggest risk / Tail risk
        if any(w in msg for w in ["risk", "biggest", "drawdown", "crash", "loss", "recession"]):
            if portfolio_context:
                curr_vol = portfolio_context.get("curr_vol", 0.15)
                enb = portfolio_context.get("effective_bets", 2.0)
                stresses = portfolio_context.get("stress_tests", [])
                worst_scenario = stresses[0] if stresses else None
                worst_desc = f"under the **{worst_scenario.get('name', 'Macro Shock')}** simulation" if worst_scenario else "during liquidity shocks"
                return (
                    f"⚠️ **Portfolio Risk Diagnosis:**\n\n"
                    f"• **Annualized Volatility (σp):** {float(curr_vol)*100:.1f}%\n"
                    f"• **Effective Bets (N_eff):** {float(enb):.1f} orthogonal factors\n"
                    f"• **Downside Sensitivity:** Your portfolio experiences peak drawdown {worst_desc}.\n\n"
                    "**Prescription:** Increase orthogonal allocation to defensive safe-havens (e.g. Gold GLD or Treasuries TLT) to expand your downside capital cushion."
                )

        # 4. Factor bets / N_eff
        if any(w in msg for w in ["bet", "bets", "neff", "effective", "factor", "eigenvalue"]):
            enb = portfolio_context.get("effective_bets", 2.0) if portfolio_context else 2.5
            n = len(portfolio_context.get("tickers", [])) if portfolio_context else 5
            return (
                f"🧮 **Effective Number of Bets (N_eff = {float(enb):.2f}):**\n\n"
                f"Although you hold **{n} distinct assets**, your portfolio only contains **{float(enb):.2f} true orthogonal risk bets**.\n\n"
                "**How it's calculated:** We perform spectral decomposition on the Pearson correlation matrix (C = VΛVᵀ) and measure the Shannon entropy of variance across eigenvalues (N_eff = exp(-Σ p_k ln p_k)).\n\n"
                "Because mega-cap equities share high systematic market beta, true diversification requires assets with low inter-correlation."
            )

        # 5. Company name / ticker resolution inquiry
        company_tickers = {
            "tata steel": ("TATASTEEL.NS", "NSE (National Stock Exchange of India) / TATASTEEL.BO"),
            "tata motors": ("TATAMOTORS.NS", "NSE (India) / TATAMOTORS.BO"),
            "tata": ("TATASTEEL.NS / TATAMOTORS.NS", "Tata Steel: TATASTEEL.NS, Tata Motors: TATAMOTORS.NS, TCS: TCS.NS (NSE/BSE)"),
            "tcs": ("TCS.NS", "NSE (India) / TCS.BO"),
            "reliance": ("RELIANCE.NS", "NSE (India) / RELIANCE.BO"),
            "infosys": ("INFY", "NYSE / INFY.NS"),
            "apple": ("AAPL", "NASDAQ"),
            "microsoft": ("MSFT", "NASDAQ"),
            "nvidia": ("NVDA", "NASDAQ"),
            "google": ("GOOGL", "NASDAQ"),
            "amazon": ("AMZN", "NASDAQ"),
            "tesla": ("TSLA", "NASDAQ"),
            "gold": ("GLD", "NYSE Arca"),
            "bitcoin": ("BTC-USD", "Crypto"),
        }
        for comp, (sym, exch) in company_tickers.items():
            if comp in msg:
                return (
                    f"🔍 **Ticker Symbol for {comp.title()}:**\n\n"
                    f"• Primary Symbol: **`{sym}`** ({exch})\n\n"
                    f"You can enter **`{sym}`** into the **Add Asset** bar in the left sidebar to add it to your portfolio universe and calculate its optimal weights!"
                )

        # 6. Live stock data inquiry
        if stock_live_data:
            reports = []
            for ticker, d in stock_live_data.items():
                price = d.get("current_price", "N/A")
                pe = d.get("trailing_pe", "N/A")
                name = d.get("name", ticker)
                beta = d.get("beta", "N/A")
                reports.append(
                    f"📈 **{name} ({ticker}):**\n"
                    f"• Price: ${price}\n"
                    f"• Trailing P/E: {pe}\n"
                    f"• Beta: {beta}\n"
                    f"• Summary: {d.get('summary', '')[:160]}..."
                )
            return "\n\n".join(reports)

        # Default intelligent assistant overview
        return (
            "🤖 **Alphawise Financial Copilot Active:**\n\n"
            "I'm continuously monitoring your active portfolio metrics. Ask me:\n"
            "• *'Why buy/sell these?'* — to view trade rationale.\n"
            "• *'What is my biggest risk?'* — to view drawdown diagnostics.\n"
            "• *'Explain factor bets'* — to understand eigenvalue entropy.\n"
            "• Or type any stock ticker like *'NVDA'* or *'AAPL'* for live fundamentals."
        )
