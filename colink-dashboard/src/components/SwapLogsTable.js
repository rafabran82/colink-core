import React from "react";

export default function SwapLogsTable({ logs = [] }) {
  return (
    <div className="swap-logs-card">
      <h2 className="section-title">Swap Logs</h2>
      <p>Swap log table temporarily minimized for debugging.</p>
      <p>Received {Array.isArray(logs) ? logs.length : 0} entries.</p>
    </div>
  );
}


