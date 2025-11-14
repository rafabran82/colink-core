import React from "react";

export default function SwapLogsView({ logs }) {
  if (!logs || logs.length === 0) {
    return <div>No recent swaps.</div>;
  }

  return (
    <div>
      <h2>Recent Swaps</h2>
      {logs.map((l, idx) => (
        <div key={idx} style={{ marginBottom: "1rem" }}>
          <div><b>Pair:</b> {l.pair || "unknown"}</div>
          <div><b>Amount:</b> {l.amount || 0}</div>
          <div><b>Timestamp:</b> {l.ts || l.timestamp || ""}</div>
        </div>
      ))}
    </div>
  );
}
