from datetime import datetime, timedelta
from typing import List

from fastapi import FastAPI\nfrom colink_core.sim.xrpl_snapshot import load_bootstrap_snapshot\nfrom colink_core.sim.engine import extract_pool_from_snapshot
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ========= Pydantic models (match React shapes) =========

class SimMeta(BaseModel):
  phase: int
  network: str
  runId: str
  lastUpdated: datetime


class PoolState(BaseModel):
  label: str
  baseSymbol: str
  quoteSymbol: str
  baseLiquidity: float
  quoteLiquidity: float
  lpTokenSupply: float
  feeBps: int
  lastUpdated: datetime


class SwapLogEntry(BaseModel):
  id: str
  timestamp: datetime
  pool: str
  fromAsset: str
  toAsset: str
  amountIn: float
  amountOut: float
  status: str


# ========= FastAPI app =========

app = FastAPI(title="COLINK Dashboard API", version="0.1.0")

# CORS so React on :3000 can talk to :8000
origins = ["http://localhost:3000"]
app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


# ========= Mock data for now (will later read from sim) =========

def _mock_meta() -> SimMeta:
  now = datetime.utcnow()
  return SimMeta(
    phase=3,
    network="testnet",
    runId="local-mock-001",
    lastUpdated=now,
  )


def _mock_pool() -> PoolState:
def _load_real_pools():
    """
    Load real COPX/COL pool from XRPL snapshot and create a synthetic
    deterministic COL/XRP pool derived from COL reserves.
    """
    snap = load_bootstrap_snapshot()
    real = extract_pool_from_snapshot(snap)

    # Real COPX/COL
    pool_real = {
        "label": "COPX/COL",
        "baseSymbol": "COPX",
        "quoteSymbol": "COL",
        "baseLiquidity": real.copx_reserve,
        "quoteLiquidity": real.col_reserve,
        "lpTokenSupply": (real.copx_reserve * real.col_reserve) ** 0.5,
        "feeBps": 30,
        "lastUpdated": datetime.utcnow().isoformat()
    }

    # Synthetic COL/XRP (deterministic)
    col_reserve = real.col_reserve
    xrp_reserve = col_reserve / 3600.0

    pool_synthetic = {
        "label": "COL/XRP",
        "baseSymbol": "COL",
        "quoteSymbol": "XRP",
        "baseLiquidity": col_reserve,
        "quoteLiquidity": xrp_reserve,
        "lpTokenSupply": (col_reserve ** 0.5),
        "feeBps": 25,
        "lastUpdated": datetime.utcnow().isoformat()
    }

    return [pool_real, pool_synthetic]
  now = datetime.utcnow()
  return PoolState(
    label="COPX/COL",
    baseSymbol="COPX",
    quoteSymbol="COL",
    baseLiquidity=125_000,
    quoteLiquidity=980_000,
    lpTokenSupply=50_000,
    feeBps=30,
    lastUpdated=now,
  )


def _mock_swaps() -> List[SwapLogEntry]:
  now = datetime.utcnow()
  return [
    SwapLogEntry(
      id="1",
      timestamp=now - timedelta(minutes=3),
      pool="COPX/COL",
      fromAsset="COPX",
      toAsset="COL",
      amountIn=1_000,
      amountOut=7_800,
      status="confirmed",
    ),
    SwapLogEntry(
      id="2",
      timestamp=now - timedelta(minutes=10),
      pool="COL/XRP",
      fromAsset="COL",
      toAsset="XRP",
      amountIn=15_000,
      amountOut=270,
      status="pending",
    ),
  ]


# ========= API endpoints =========


@app.get("/api/sim/meta", response_model=SimMeta)
def get_sim_meta() -> SimMeta:
  # TODO: later wire this to real Phase 3 run metadata
  return _mock_meta()


@app.get("/api/pools/state", response_model=List[PoolState])
def get_pools_state() -> List[PoolState]:
  # TODO: later wire this to engine/xrpl_snapshot outputs
  return [_mock_pool(), _mock_pool()]


@app.get("/api/swaps/recent", response_model=List[SwapLogEntry])
def get_recent_swaps() -> List[SwapLogEntry]:
  # TODO: later wire this to recent sim swaps
  return _mock_swaps()



