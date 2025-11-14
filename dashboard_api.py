from datetime import datetime, timedelta
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import Phase-3 snapshot + real pool extractor
from colink_core.sim.xrpl_snapshot import load_bootstrap_snapshot
from colink_core.sim.engine import extract_pool_from_snapshot

# Import dashboard models
from pydantic import BaseModel


# -----------------------------
# Pydantic response models
# -----------------------------

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
    lastUpdated: str


class SwapLogEntry(BaseModel):
    id: str
    timestamp: datetime
    pool: str
    fromAsset: str
    toAsset: str
    amountIn: float
    amountOut: float
    status: str


# -----------------------------
# FastAPI Setup
# -----------------------------

app = FastAPI(title="COLINK Dashboard API", version="0.1.0")

origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Mock metadata (keep for now)
# -----------------------------

def _mock_meta() -> SimMeta:
    now = datetime.utcnow()
    return SimMeta(
        phase=3,
        network="testnet",
        runId="local-mock-001",
        lastUpdated=now,
    )


# -----------------------------
# Real pools loader (Phase-3)
# -----------------------------

def _load_real_pools() -> List[PoolState]:
    """
    Build two pools:
    1) Real COPX/COL pool from XRPL snapshot
    2) Synthetic COL/XRP pool derived deterministically
    """
    snap = load_bootstrap_snapshot()
    real = extract_pool_from_snapshot(snap)

    # Real XRPL pool
    pool_real = PoolState(
        label="COPX/COL",
        baseSymbol="COPX",
        quoteSymbol="COL",
        baseLiquidity=real.copx_reserve,
        quoteLiquidity=real.col_reserve,
        lpTokenSupply=(real.copx_reserve * real.col_reserve) ** 0.5,
        feeBps=30,
        lastUpdated=datetime.utcnow().isoformat(),
    )

    # Synthetic COL/XRP
    col_reserve = real.col_reserve
    xrp_reserve = col_reserve / 3600.0

    pool_synth = PoolState(
        label="COL/XRP",
        baseSymbol="COL",
        quoteSymbol="XRP",
        baseLiquidity=col_reserve,
        quoteLiquidity=xrp_reserve,
        lpTokenSupply=col_reserve ** 0.5,
        feeBps=25,
        lastUpdated=datetime.utcnow().isoformat(),
    )

    return [pool_real, pool_synth]


# -----------------------------
# Mock swap logs for now
# -----------------------------

def _mock_swaps() -> List[SwapLogEntry]:
    now = datetime.utcnow()
    return [
        SwapLogEntry(
            id="1",
            timestamp=now - timedelta(minutes=3),
            pool="COPX/COL",
            fromAsset="COPX",
            toAsset="COL",
            amountIn=1000,
            amountOut=7800,
            status="confirmed",
        ),
        SwapLogEntry(
            id="2",
            timestamp=now - timedelta(minutes=10),
            pool="COL/XRP",
            fromAsset="COL",
            toAsset="XRP",
            amountIn=15000,
            amountOut=270,
            status="pending",
        ),
    ]


# -----------------------------
# API Endpoints
# -----------------------------

@app.get("/api/sim/meta", response_model=SimMeta)
def get_sim_meta() -> SimMeta:
    return _mock_meta()


@app.get("/api/pools/state", response_model=List[PoolState])
def get_pools_state() -> List[PoolState]:
    return _load_real_pools()


@app.get("/api/swaps/recent", response_model=List[SwapLogEntry])
def get_recent_swaps() -> List[SwapLogEntry]:
    return _mock_swaps()

