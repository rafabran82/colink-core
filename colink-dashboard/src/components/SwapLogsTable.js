import React, { useEffect, useState } from "react";

export default function SwapLogsTable({ logs }) {
  const [flashMap, setFlashMap] = useState({});

  useEffect(() => {
    const next = {};
    logs.forEach((log) => { next[log.id] = true; });
    setFlashMap(next);

    const timer = setTimeout(() => {
      setFlashMap({});
    }, 1200);

    return () => clearTimeout(timer);
  }, [logs]);

  return (
    <table style={{ width: "100%", marginTop: "12px", fontSize: "0.9rem" }}>
      <thead>
        <tr>
          <th>ID</th>
          <th>Pool</th>
          <th>From</th>
          <th>To</th>
          <th>Amount In</th>
          <th>Amount Out</th>
          <th>Status</th>
          <th>Time</th>
        </tr>
      </thead>

      <tbody>
        {logs.map((log) => (
          <tr
            key={log.id}
            className={flashMap[log.id] ? "flash-update" : ""}
            style={{ borderBottom: "1px solid #333" }}
          >
            <td>{log.id}</td>
            <td>{log.pool}</td>
            <td>{log.fromAsset}</td>
            <td>{log.toAsset}</td>
            <td>{log.amountIn}</td>
            <td>{log.amountOut}</td>
            <td>{log.status}</td>
            <td>{new Date(log.timestamp).toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
