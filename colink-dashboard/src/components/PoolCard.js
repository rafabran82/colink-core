import React from "react";


function PoolCard({ pools }) {
  if (!pools || pools.length === 0) {
    return <p>No pool data available.</p>;
  }

  return (
    <div style={{
      display: "flex",
      flexWrap: "wrap",
      gap: "16px"
    }}>
      {pools.map((p, i) => (
        <div
          key={i}
          style={{
            border: "1px solid #444",
            padding: "16px",
            borderRadius: "12px",
            minWidth: "280px",
            backgroundColor: "var(--card-bg)",
            color: "var(--text-primary)",
          }}
        >
          <h3 style={{ marginTop: 0 }}>{p.label}</h3>

          <p><strong>Base:</strong> {p.baseSymbol}</p>
          <p><strong>Quote:</strong> {p.quoteSymbol}</p>

          <p><strong>Base Liquidity:</strong> {p.baseLiquidity.toLocaleString()}</p>
          <p><strong>Quote Liquidity:</strong> {p.quoteLiquidity.toLocaleString()}</p>

          <p><strong>LP Supply:</strong> {p.lpTokenSupply.toLocaleString()}</p>
          <p><strong>Fee:</strong> {p.feeBps} bps</p>

          {"syntheticPrice" in p && (
            <p><strong>Synthetic Price:</strong> {p.syntheticPrice.toFixed(6)}</p>
          )}

          <p style={{ fontSize: "0.75rem", opacity: 0.7 }}>
            Updated {p.lastUpdated}
          </p>
        </div>
      ))}
    </div>
  );
}

export default PoolCard;

