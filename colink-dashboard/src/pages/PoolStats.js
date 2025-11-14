import React, { useEffect, useState } from "react";
import { fetchPools } from "../api/pools";

function PoolStats() {
  const [pools, setPools] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const list = await fetchPools();
        setPools(list);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <p style={{ padding: "20px" }}>Loading pool stats…</p>;
  }

  if (!loading && pools.length === 0) {
    return <p style={{ padding: "20px" }}>No pools available.</p>;
  }

  return (
    <div style={{ padding: "20px" }}>
      <h1>Pool Statistics</h1>

      {pools.map((p, i) => {
        const updated = new Date(p.lastUpdated).toLocaleString();

        return (
          <div
            key={i}
            style={{
              marginTop: "22px",
              padding: "18px",
              background: "rgba(255,255,255,0.05)",
              border: "1px solid #666",
              borderRadius: "8px",
            }}
          >
            <h2>{p.label}</h2>

            <p><strong>Base:</strong> {p.baseSymbol} - Liquidity: {p.baseLiquidity.toLocaleString()}</p>
            <p><strong>Quote:</strong> {p.quoteSymbol} - Liquidity: {p.quoteLiquidity.toLocaleString()}</p>
            <p><strong>LP Supply:</strong> {p.lpTokenSupply.toLocaleString()}</p>
            <p><strong>Fee:</strong> {p.feeBps} bps</p>

            <p style={{ fontSize: "0.85rem", opacity: 0.7 }}>
              Updated: {updated}
            </p>
          </div>
        );
      })}
    </div>
  );
}

export default PoolStats;
