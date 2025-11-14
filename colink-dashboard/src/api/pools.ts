import axios from "axios";

export interface PoolState {
  label: string;
  baseSymbol: string;
  quoteSymbol: string;
  baseLiquidity: number;
  quoteLiquidity: number;
  lpTokenSupply: number;
  feeBps: number;
  lastUpdated: string;
}

export interface SimMeta {
  simTimestamp: string;
  backend: string;
  backendVersion: string;
}

export async function fetchPools(): Promise<PoolState[]> {
  const res = await axios.get("http://127.0.0.1:8000/api/pools/state");
  return res.data;
}

export async function fetchSimMeta(): Promise<SimMeta | null> {
  try {
    const res = await axios.get("http://127.0.0.1:8000/api/sim/meta");
    return res.data;
  } catch {
    return null;
  }
}
