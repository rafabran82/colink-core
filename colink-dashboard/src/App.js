import React, { useEffect, useState } from "react";
import "./App.css";
import { fetchSimMeta } from "./api/meta";
import { fetchPools } from "./api/pools";
import { fetchSwapLogs } from "./api/logs";

// ---------------------------------------
//  Helper: Compute newest timestamp
// ---------------------------------------
function computeLatestTimestamp(simMeta, pools, swaps) {
  const ts = [];

  if (simMeta?.lastUpdated) ts.push(new Date(simMeta.lastUpdated));

  if (Array.isArray(pools)) {
    pools.forEach(p => {
      if (p.lastUpdated) ts.push(new Date(p.lastUpdated));
    });
  }

  if (Array.isArray(swaps)) {
    swaps.forEach(s => {
      const t = s.timestamp || s.executed_at;
      if (t) ts.push(new Date(t));
    });
  }

  if (ts.length === 0) return "N/A";

  const latest = ts.reduce((a, b) => (a > b ? a : b));
  return latest.toLocaleString();
}

// ---------------------------------------
//  Main Component
// ---------------------------------------
function App() {
  const [meta, setMeta] = useState({});
  const [pools, setPools] = useState([]);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    loadAll();
  }, []);

  async function loadAll() {
    try {
      const [m, p, l] = await Promise.all([
        fetchSimMeta(),
        fetchPools(),
        fetchSwapLogs(),
      ]);

      setMeta(m || {});
      setPools(p || []);
      setLogs(l || []);
    } catch (err) {
      console.error("Dashboard loadAll failed", err);
    }
  }

  const globalTimestamp = computeLatestTimestamp(meta, pools, logs);

  return (
    <div
      className="App"
      style={{
        background: "black",
        color: "white",
        minHeight: "100vh",
        padding: "2rem",
      }}
    >
      <h1 className="app-title">COLINK Dashboard</h1>
      <div className="global-status">Data as of: {globalTimestamp}</div>

      {/* --- POOL STATE --- */}
      <h2>Pool State</h2>
      {pools.length === 0 ? (
        <p>No pool data available.</p>
      ) : (
        pools.map((pool, idx) => (
          <div
            key={idx}
            style={{
              border: "1px solid #333",
              borderRadius: "8px",
              padding: "1rem",
              marginBottom: "1rem",
              background: "#111",
            }}
          >
            <h3>{pool.label}</h3>
            <p>
              <b>Base:</b> {pool.baseSymbol} — Liquidity:{" "}
              {pool.baseLiquidity.toLocaleString()}
            </p>
            <p>
              <b>Quote:</b> {pool.quoteSymbol} — Liquidity:{" "}
              {pool.quoteLiquidity.toLocaleString()}
            </p>
            <p>
              <b>LP Supply:</b> {pool.lpTokenSupply.toLocaleString()}
            </p>
            <p>
              <b>Fee:</b> {pool.feeBps} bps
            </p>
            <p>
              <small>
                Updated: {new Date(pool.lastUpdated).toLocaleString()}
              </small>
            </p>
          </div>
        ))
      )}

      {/* --- SWAP LOGS --- */}
      <h2>Swap Logs</h2>
      {logs.length === 0 ? (
        <div style={{ padding: "1rem", background: "#111", borderRadius: "8px" }}>
          <b>No swap logs yet</b>
        </div>
      ) : (
        <table
          style={{
            width: "100%",
            marginTop: "1rem",
            background: "#111",
            borderCollapse: "collapse",
          }}
        >
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
            {logs.map((log, idx) => (
              <tr key={idx} style={{ borderTop: "1px solid #333" }}>
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
      )}
    </div>
  );
}

export default App;
