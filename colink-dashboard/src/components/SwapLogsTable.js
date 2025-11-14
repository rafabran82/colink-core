import React from "react";

function SwapLogsTable({ logs }) {
  const border = "var(--card-border)";
  const headerBg = "var(--card-bg)";
  const muted = "var(--text-muted)";
  const fg = "var(--text)";

  return (
    <table
      style={{
        width: "100%",
        borderCollapse: "collapse",
        marginTop: "12px",
        fontSize: "0.95rem",
        color: fg,
      }}
    >
      <thead>
        <tr
          style={{
            backgroundColor: headerBg,
            borderBottom: `1px solid ${border}`,
          }}
        >
          <th style={{ textAlign: "left", padding: "6px" }}>Time</th>
          <th style={{ padding: "6px" }}>Pool</th>
          <th style={{ padding: "6px" }}>Swap</th>
          <th style={{ padding: "6px", textAlign: "right" }}>In</th>
          <th style={{ padding: "6px", textAlign: "right" }}>Out</th>
          <th style={{ textAlign: "left", padding: "6px" }}>Status</th>
        </tr>
      </thead>

      <tbody>
        {logs.map((log) => (
          <tr
            key={log.id}
            style={{
              borderTop: `1px solid ${border}`,
            }}
          >
            <td style={{ padding: "6px", color: muted }}>
              {new Date(log.timestamp).toLocaleTimeString()}
            </td>

            <td style={{ padding: "6px" }}>{log.pool}</td>

            <td style={{ padding: "6px" }}>
              {log.fromAsset} → {log.toAsset}
            </td>

            <td
              style={{
                padding: "6px",
                textAlign: "right",
              }}
            >
              {log.amountIn.toLocaleString()}
            </td>

            <td
              style={{
                padding: "6px",
                textAlign: "right",
              }}
            >
              {log.amountOut.toLocaleString()}
            </td>

            <td
              style={{
                padding: "6px",
                color:
                  log.status === "confirmed"
                    ? "var(--accent-green)"
                    : "var(--accent-orange)",
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
