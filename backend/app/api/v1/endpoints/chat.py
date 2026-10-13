"""
Alphawise Chat & AI Copilot Endpoint
====================================
Provides endpoints for:
  1. Interactive AI Copilot chat (/api/v1/chat): answers questions based on
     the user's invested stocks, optimal allocations, risk statistics,
     and general stock queries with live yfinance data.
  2. Dynamic Commentary Regeneration (/api/v1/memo/regenerate): allows the user
     to re-roll the Institutional Memo or WallStreetBets Roast on demand.
"""

import logging
from typing import Any, Dict
from fastapi import APIRouter, HTTPException

from app.models.request import ChatRequest, RegenerateMemoRequest
from app.models.response import ChatResponse, AiCommentary, InstitutionalMemo, RoastMemo
from app.services.llm_service import LLMService
from app.services.ai_diagnostics import DiagnosticsEngine

logger = logging.getLogger("alphawise.chat")
router = APIRouter(tags=["AI Copilot"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Interactive Portfolio & Stock Copilot Chat",
)
async def chat_with_copilot(req: ChatRequest):
    """
    Multi-turn financial chat co-pilot:
      - Uses active portfolio holdings & metrics for portfolio queries.
      - Resolves stock queries using real-time yfinance market metrics.
      - Powered by Groq (Llama 3.3 70B) or OpenAI-compatible backend.
    """
    try:
        history_dicts = [h.model_dump() for h in req.conversation_history]
        result = await LLMService.chat_copilot(
            message=req.message,
            conversation_history=history_dicts,
            portfolio_context=req.portfolio_context,
        )
        return ChatResponse(
            status="success",
            reply=result["reply"],
            mentioned_tickers=result.get("mentioned_tickers", []),
            live_data=result.get("live_data", {}),
            model=result.get("model", "unknown"),
        )
    except Exception as exc:
        logger.exception("Error in copilot chat: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Copilot inference error: {str(exc)}",
        )


@router.post(
    "/memo/regenerate",
    summary="Regenerate Institutional Memo or FinTwit Roast with AI",
)
async def regenerate_memos(req: RegenerateMemoRequest):
    """
    Regenerates the Institutional Memo or WSB Roast for an existing portfolio.
    Falls back to deterministic generation if LLM is unavailable.
    """
    ctx = req.portfolio_context
    tickers = ctx.get("tickers", [])
    curr_weights = ctx.get("curr_weights", {})
    opt_weights = ctx.get("opt_weights", {})
    curr_ret = float(ctx.get("curr_ret", 0.10))
    curr_vol = float(ctx.get("curr_vol", 0.15))
    curr_sharpe = float(ctx.get("curr_sharpe", 0.8))
    opt_ret = float(ctx.get("opt_ret", 0.15))
    opt_vol = float(ctx.get("opt_vol", 0.12))
    opt_sharpe = float(ctx.get("opt_sharpe", 1.2))
    enb = float(ctx.get("effective_bets", 2.0))
    health = ctx.get("health_score", {"grade": "B", "score": 75, "rating": "Balanced"})
    rebalances = ctx.get("rebalance_actions", [])
    stresses = ctx.get("stress_tests", [])

    # Default fallback from rule engine
    baseline = DiagnosticsEngine.generate_plain_english_memos(
        tickers=tickers,
        curr_weights=curr_weights,
        opt_weights=opt_weights,
        curr_ret=curr_ret,
        curr_vol=curr_vol,
        curr_sharpe=curr_sharpe,
        opt_ret=opt_ret,
        opt_vol=opt_vol,
        opt_sharpe=opt_sharpe,
        effective_bets=enb,
        health_score=health,
        rebalance_actions=rebalances,
        stress_tests=stresses,
    )

    inst_memo = baseline["institutional_memo"]
    roast_memo = baseline["roast_memo"]

    # Try Groq LLM generation if configured
    if LLMService.is_configured():
        if req.mode in ("institutional", "both"):
            llm_inst = await LLMService.generate_institutional_memo(
                tickers=tickers,
                curr_weights=curr_weights,
                opt_weights=opt_weights,
                curr_ret=curr_ret,
                curr_vol=curr_vol,
                curr_sharpe=curr_sharpe,
                opt_ret=opt_ret,
                opt_vol=opt_vol,
                opt_sharpe=opt_sharpe,
                effective_bets=enb,
                health_score=health,
                rebalance_actions=rebalances,
                stress_tests=stresses,
            )
            if llm_inst:
                inst_memo = llm_inst

        if req.mode in ("roast", "both"):
            llm_roast = await LLMService.generate_roast_memo(
                tickers=tickers,
                curr_weights=curr_weights,
                opt_weights=opt_weights,
                curr_ret=curr_ret,
                curr_vol=curr_vol,
                curr_sharpe=curr_sharpe,
                opt_sharpe=opt_sharpe,
                effective_bets=enb,
                rebalance_actions=rebalances,
            )
            if llm_roast:
                roast_memo = llm_roast

    return {
        "status": "success",
        "institutional_memo": inst_memo,
        "roast_memo": roast_memo,
        "source": "groq_llm" if LLMService.is_configured() else "rule_engine",
    }
