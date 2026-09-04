import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add ecCodes and C runtimes to DLL directory on Windows
_BIN_DIR = Path(__file__).resolve().parents[3] / "forecast-bust-sentinel" / "scratch" / "env_eccodes" / "Library" / "bin"
if _BIN_DIR.exists():
    if str(_BIN_DIR) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = str(_BIN_DIR) + os.pathsep + os.environ.get("PATH", "")
    try:
        os.add_dll_directory(str(_BIN_DIR))
    except Exception:
        pass

from backend.app.agents.forecast_bust_agent import ForecastBustAgent
from backend.app.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def default_agent() -> ForecastBustAgent:
    """Default ForecastBustAgent fixture."""
    return ForecastBustAgent()
