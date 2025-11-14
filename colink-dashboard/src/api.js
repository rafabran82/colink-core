const API_BASE =
  process.env.REACT_APP_COLINK_API_BASE || "http://localhost:8000";

const mockPool = {
  label: "COPX/COL",
  baseSymbol: "COPX",
  quoteSymbol: "COL",
  baseLiquidity: 125000,
  quoteLiquidity: 980000,
  lpTokenSupply: 50000,
  feeBps: 30,
  lastUpdated: new Date().toISOString(),
};

const mockSwapLogs = [
  {
    id: 1,
    timestamp: new Date(Date.now() - 1000 * 60 * 3).toISOString(),
    pool: "COPX/COL",
    fromAsset: "COPX",
    toAsset: "COL",
    amountIn: 1000,
    amountOut: 7800,
    status: "confirmed",
  },
  {
    id: 2,
    timestamp: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
    pool: "COL/XRP",
    fromAsset: "COL",
    toAsset: "XRP",
    amountIn: 15000,
    amountOut: 270,
    status: "pending",
  },
];

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function getJson(path, fallback) {
  try {
    const resp = await fetch(`${API_BASE}${path}`);
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`);
    }
    const data = await resp.json();
    return data;
  } catch (err) {
    console.warn("API fallback for", path, err?.message || err);
    await delay(150);
    return fallback;
  }
}

// NOTE: These helpers try to be tolerant about backend response shapes
// so you can evolve the API without breaking the dashboard.

export async function fetchPoolState() {
  const data = await getJson("/api/pools/state", mockPool);

  // If backend returns an array, pick the first pool
  if (Array.isArray(data)) {
    return data[0] || mockPool;
  }

  // If backend wraps in { pools: [...] }
  if (data && Array.isArray(data.pools)) {
    return data.pools[0] || mockPool;
  }

  // Assume it already matches the pool shape
  return data || mockPool;
}

export async function fetchSwapLogs() {
  const data = await getJson("/api/swaps/recent", mockSwapLogs);

  let arr = data;

  // If backend wraps in { swaps: [...] }
  if (data && Array.isArray(data.swaps)) {
    arr = data.swaps;
  }

  if (!Array.isArray(arr)) {
    return mockSwapLogs;
  }

  return arr;
}

export async function fetchSimMeta() {
  const fallback = {
    phase: 3,
    network: "testnet",
    runId: "local-mock-001",
    lastUpdated: new Date().toISOString(),
  };

  const data = await getJson("/api/sim/meta", fallback);
  return {
    phase: data.phase ?? fallback.phase,
    network: data.network ?? fallback.network,
    runId: data.runId ?? fallback.runId,
    lastUpdated: data.lastUpdated ?? fallback.lastUpdated,
  };
}
