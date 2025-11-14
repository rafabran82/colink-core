import React from "react";

function SwapLogsTable({ logs }) {
  return (
    <table
      style={{
        width: "100%",
        maxWidth: "720px",
        marginTop: "12px",
        borderCollapse: "collapse",
        fontSize: "0.9rem",
      }}
    >
      <thead>
        <tr>
          <th style={{ textAlign: "left", padding: "6px" }}>Time</th>
          <th style={{ textAlign: "left", padding: "6px" }}>Pool</th>
          <th style={{ textAlign: "left", padding: "6px" }}>Swap</th>
          <th style={{ textAlign: "right", padding: "6px" }}>In</th>
          <th style={{ textAlign: "right", padding: "6px" }}>Out</th>
          <th style={{ textAlign: "left", padding: "6px" }}>Status</th>
        </tr>
      </thead>

      <tbody>
        {logs.map((log) => (
          <tr key={log.id} style={{ borderTop: "1px solid #ddd" }}>
            <td style={{ padding: "6px" }}>
              {new Date(log.timestamp).toLocaleTimeString()}
            </td>
            <td style={{ padding: "6px" }}>{log.pool}</td>
            <td style={{ padding: "6px" }}>
              {log.fromAsset} → {log.toAsset}
            </td>
            <td style={{ padding: "6px", textAlign: "right" }}>
              {log.amountIn.toLocaleString()}
            </td>
            <td style={{ padding: "6px", textAlign: "right" }}>
              {log.amountOut.toLocaleString()}
            </td>
            <td
              style={{
                padding: "6px",
                color: log.status === "confirmed" ? "green" : "orange",
              }}
            >
              {log.status}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default SwapLogsTable;
