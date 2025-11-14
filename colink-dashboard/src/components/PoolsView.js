import React from "react";

export default function PoolsView({ pools }) {
  if (!pools || pools.length === 0) {
    return <div>No pools available.</div>;
  }

  return (
    <div>
      <h2>Pools</h2>
      {pools.map((p, idx) => (
        <div key={idx} style={{ marginBottom: "1rem" }}>
          <div><b>Pool:</b> {p.name || "unknown"}</div>
          <div><b>Volume:</b> {p.volume || 0}</div>
          <div><b>Liquidity:</b> {p.liquidity || 0}</div>
        </div>
      ))}
    </div>
  );
}
