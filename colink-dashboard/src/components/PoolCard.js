import React from "react";

export default function PoolCard({ pool }) {
  if (!pool) return null;

  const {
    label,
    baseSymbol,
    quoteSymbol,
    baseLiquidity,
    quoteLiquidity,
    lpTokenSupply,
    feeBps,
    lastUpdated
  } = pool;

  const updated = new Date(lastUpdated).toLocaleString();

  return (
  <div
    style={{
      padding: "16px",
      marginBottom: "20px",
      borderRadius: "8px",
      border: "1px solid #666",
      background: "rgba(255,255,255,0.04)",
      lineHeight: "1.45",
      fontSize: "0.92rem"
    }}
  >
      <h3>{label}</h3>
      <p><strong>Base:</strong> {baseSymbol} — Liquidity: {baseLiquidity.toLocaleString()}</p>
      <p><strong>Quote:</strong> {quoteSymbol} — Liquidity: {quoteLiquidity.toLocaleString()}</p>
      <p><strong>LP Supply:</strong> {lpTokenSupply.toLocaleString()}</p>
      <p><strong>Fee:</strong> {feeBps} bps</p>
      <p style={{ fontSize: "0.8rem", opacity: 0.7 }}>
        Updated: {updated}
      </p>
    </div>
  );
}

