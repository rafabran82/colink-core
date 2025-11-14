import React from "react";

function SwapLogsTable({ logs }) {
  if (!logs || logs.length === 0) {
    return <p>No recent swaps.</p>;
  }

  return (
    <table
      style={{
        width: "100%",
        borderCollapse: "collapse",
        marginTop: "12px",
      }}
    >
      <thead>
        <tr style={{ borderBottom: "2px solid #ccc" }}>
          <th>ID</th>
          <th>Timestamp</th>
          <th>Pool</th>
          <th>From</th>
          <th>To</th>
          <th>Amount In</th>
          <th>Amount Out</th>
          <th>Status</th>
        </tr>
      </thead>

      <tbody>
        {logs.map((log) => (
          <tr key={log.id} style={{ borderBottom: "1px solid #eee" }}>
            <td>{log.id}</td>
            <td>{new Date(log.timestamp).toLocaleString()}</td>
            <td>{log.pool}</td>
            <td>{log.fromAsset}</td>
            <td>{log.toAsset}</td>
            <td>{log.amountIn}</td>
            <td>{log.amountOut}</td>
            <td>{log.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default SwapLogsTable;
