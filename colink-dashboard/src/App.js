import React, { useEffect, useState } from "react";
import "./App.css";

import { fetchSimMeta } from "./api/meta";
import { fetchPools } from "./api/pools";
import { fetchSwapLogs } from "./api/logs";

/* ---------------------------------------------
   computeLatestTimestamp
---------------------------------------------- */
function computeLatestTimestamp(simMeta, pools, swaps) {
  const ts = [];

  if (simMeta?.lastUpdated) ts.push(new Date(simMeta.lastUpdated));

  if (Array.isArray(pools)) {
    pools.forEach((p) => {
      if (p.lastUpdated) ts.push(new Date(p.lastUpdated));
    });
  }

  if (Array.isArray(swaps)) {
    swaps.forEach((s) => {
      const t = s.timestamp || s.executed_at;
      if (t) ts.push(new Date(t));
    });
  }

  if (ts.length === 0) return "N/A";
  const latest = ts.reduce((a, b) => (a > b ? a : b));
  return latest.toLocaleString();
}

/* ---------------------------------------------
   markFlashes
---------------------------------------------- */
function markFlashes(oldArr, newArr, keyFn) {
  const oldMap = Object.fromEntries((oldArr || []).map((o) => [keyFn(o), o]));

  return (newArr || []).map((n) => {
    const key = keyFn(n);
    const old = oldMap[key];

    if (!old) return { ...n, __flash: true };
    if (JSON.stringify(old) !== JSON.stringify(n))
      return { ...n, __flash: true };

    return { ...n, __flash: false };
  });
}

/* ---------------------------------------------
   App
---------------------------------------------- */
function App() {
  const [simMeta, setSimMeta] = useState({});
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

      setSimMeta(m || {});
      setPools((prev) => markFlashes(prev, p || [], (x) => x.label));
      setLogs((prev) => markFlashes(prev, l || [], (x) => x.id));
    } catch (err) {
      console.error("Dashboard loadAll failed", err);
    }
  }

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

      {/* Global Status Line */}
      <div className="global-status" style={{ marginBottom: "1rem" }}>
        Data as of: {computeLatestTimestamp(simMeta, pools, logs)}
      </div>

      {/* Pool State */}
      <h2>Pool State</h2>

      {pools.length === 0 ? (
        <p>No pool data available.</p>
      ) : (
        pools.map((pool, idx) => (
          <div
            key={idx}
            className={pool.__flash ? "flash" : ""}
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

      {/* Swap Logs */}
      <h2>Swap Logs</h2>

      {logs.length === 0 ? (
        <div
          style={{
            padding: "1rem",
            background: "#111",
            borderRadius: "8px",
          }}
        >
          <b>No swap logs yet</b>
          <p>Run a simulation or on-ledger test swap to see recent activity.</p>
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
              <tr
                key={idx}
                className={log.__flash ? "flash" : ""}
                style={{
                  borderTop: "1px solid #333",
                }}
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
      )}
    </div>
  );
}

export default App;