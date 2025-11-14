import React from "react";

export default function SwapLogsTable({ logs }) {
  if (!logs || logs.length === 0) {
    return <p>No swap logs available.</p>;
  }

  return (
    <table
      style={{
        width: "100%",
        marginTop: "12px",
        borderCollapse: "collapse",
        fontSize: "0.9rem",
      }}
    >
      <thead>
        <tr style={{ borderBottom: "1px solid #555" }}>
          <th style={{ padding: "6px" }}>Time</th>
          <th style={{ padding: "6px" }}>Pool</th>
          <th style={{ padding: "6px" }}>Swap</th>
          <th style={{ padding: "6px" }}>In</th>
          <th style={{ padding: "6px" }}>Out</th>
          <th style={{ padding: "6px" }}>Status</th>
        </tr>
      </thead>

      <tbody>
        {logs.map((log, i) => {
          const ts = new Date(log.timestamp).toLocaleTimeString();
          const poolLabel = `${log.pool.baseSymbol}/${log.pool.quoteSymbol}`;
          const swapDir = `${log.inputSymbol} → ${log.outputSymbol}`;

          return (
            <tr key={i} style={{ borderBottom: "1px solid #333" }}>
              <td style={{ padding: "6px" }}>{ts}</td>
              <td style={{ padding: "6px" }}>{poolLabel}</td>
              <td style={{ padding: "6px" }}>{swapDir}</td>
              <td style={{ padding: "6px" }}>{log.inputAmount.toLocaleString()}</td>
              <td style={{ padding: "6px" }}>{log.outputAmount.toLocaleString()}</td>
              <td
                style={{
                  padding: "6px",
                  color: log.confirmed ? "lightgreen" : "orange",
                }}
              >
                {log.confirmed ? "confirmed" : "pending"}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
