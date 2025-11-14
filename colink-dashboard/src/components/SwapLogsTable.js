import React from "react";

function formatTimestamp(value) {
  if (!value) return "";
  try {
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) {
      return String(value);
    }
    return d.toLocaleString();
  } catch {
    return String(value);
  }
}

export default function SwapLogsTable({ logs = [] }) {
  const hasLogs = Array.isArray(logs) && logs.length > 0;

  return (
    <div className="swap-logs-card">
      <h2 className="section-title">Swap Logs</h2>
      {!hasLogs && (
        <div className="empty-state">No recent swaps.</div>
      )}
      {hasLogs && (
        <div className="table-wrapper">
          <table className="swap-logs-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Pair</th>
                <th>Amount In</th>
                <th>Amount Out</th>
                <th>Tx Hash</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((swap, idx) => (
                <tr key={swap.id ?? swap.tx_hash ?? swap.txid ?? idx}>
                  <td>{formatTimestamp(swap.timestamp || swap.executed_at)}</td>
                  <td>
                    {swap.pair ||
                      `${swap.base_symbol ?? ""}/${swap.quote_symbol ?? ""}`}
                  </td>
                  <td>{swap.amount_in ?? swap.input_amount ?? ""}</td>
                  <td>{swap.amount_out ?? swap.output_amount ?? ""}</td>
                  <td className="tx-hash">
                    {swap.tx_hash || swap.txid || "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
