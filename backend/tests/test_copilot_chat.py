import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starlette.testclient import TestClient
from app.main import app
from app.services.llm_service import LLMService

client = TestClient(app)


def test_copilot_chat_endpoint_fallback():
    """Verify chat endpoint returns a valid response even without API key."""
    payload = {
        "message": "What is the Sharpe ratio?",
        "conversation_history": [],
        "portfolio_context": None,
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "reply" in data
    assert isinstance(data["reply"], str)
    assert len(data["reply"]) > 0


def test_copilot_chat_with_portfolio_context():
    """Verify chat endpoint handles portfolio context gracefully."""
    payload = {
        "message": "Why are you recommending to sell AAPL?",
        "conversation_history": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hello! How can I assist you with your portfolio?"}
        ],
        "portfolio_context": {
            "tickers": ["AAPL", "MSFT", "GOOGL"],
            "curr_weights": {"AAPL": 0.5, "MSFT": 0.3, "GOOGL": 0.2},
            "opt_weights": {"AAPL": 0.2, "MSFT": 0.5, "GOOGL": 0.3},
            "curr_sharpe": 1.1,
            "opt_sharpe": 1.6,
        },
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "reply" in data


def test_memo_regenerate_endpoint():
    """Verify memo regeneration endpoint works with fallback or LLM."""
    payload = {
        "mode": "both",
        "portfolio_context": {
            "tickers": ["AAPL", "NVDA", "MSFT"],
            "curr_weights": {"AAPL": 0.4, "NVDA": 0.4, "MSFT": 0.2},
            "opt_weights": {"AAPL": 0.3, "NVDA": 0.3, "MSFT": 0.4},
            "curr_ret": 0.25,
            "curr_vol": 0.28,
            "curr_sharpe": 0.89,
            "opt_ret": 0.26,
            "opt_vol": 0.20,
            "opt_sharpe": 1.30,
            "effective_bets": 1.45,
            "health_score": {"grade": "C", "score": 58, "rating": "Concentrated"},
            "rebalance_actions": [
                {"ticker": "NVDA", "action": "SELL", "delta_weight": -0.1},
                {"ticker": "MSFT", "action": "BUY", "delta_weight": 0.2}
            ],
            "stress_tests": []
        }
    }
    response = client.post("/api/v1/memo/regenerate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "institutional_memo" in data
    assert "roast_memo" in data
    assert data["institutional_memo"]["health_grade"] in ["A+", "A", "B", "C", "D", "F"]
    assert "headline" in data["roast_memo"]


def test_ticker_extraction():
    """Test extracting tickers from user query."""
    tickers = LLMService._extract_tickers("Can you analyze $TSLA and AAPL vs SPY?")
    assert "TSLA" in tickers or "AAPL" in tickers or "SPY" in tickers
