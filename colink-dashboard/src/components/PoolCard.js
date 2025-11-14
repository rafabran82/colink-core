import React from "react";

function PoolCard({ pool }) {
  return (
    <div
      style={{
        marginTop: "8px",
        padding: "12px 16px",
        border: "1px solid #dddddd",
        borderRadius: "8px",
        maxWidth: "420px",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: "8px",
        }}
      >
        <strong>{pool.label}</strong>
        <span style={{ fontSize: "0.85rem", color: "#555" }}>
          Fee: {(pool.feeBps / 100).toFixed(2)}%
        </span>
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: "0.95rem",
        }}
      >
        <span>{pool.baseSymbol} reserve</span>
        <span>{pool.baseLiquidity.toLocaleString()}</span>
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: "0.95rem",
          marginTop: "4px",
        }}
      >
        <span>{pool.quoteSymbol} reserve</span>
        <span>{pool.quoteLiquidity.toLocaleString()}</span>
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: "0.95rem",
          marginTop: "4px",
        }}
      >
        <span>LP supply</span>
        <span>{pool.lpTokenSupply.toLocaleString()}</span>
      </div>

      <div style={{ marginTop: "6px", fontSize: "0.8rem", color: "#777" }}>
        Updated:{" "}
        {new Date(pool.lastUpdated).toLocaleTimeString(undefined, {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })}
      </div>
    </div>
  );
}

export default PoolCard;
