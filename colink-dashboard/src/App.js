import React, { useEffect, useState } from "react";
import "./App.css";

import { fetchSimMeta } from "./api/meta";
import { fetchPools } from "./api/pools";
import { fetchSwapLogs } from "./api/logs";
import SwapDetailsModal from "./components/SwapDetailsModal";

function computeLatestTimestamp(meta, pools, swaps) {
  const ts = [];

  if (meta?.lastUpdated) ts.push(new Date(meta.lastUpdated));

  if (Array.isArray(pools))
    pools.forEach((p) => p.lastUpdated && ts.push(new Date(p.lastUpdated)));

  if (Array.isArray(swaps))
    swaps.forEach((s) => {
      const t = s.timestamp || s.executed_at;
      if (t) ts.push(new Date(t));
    });

  if (ts.length === 0) return null;
  return ts.reduce((a, b) => (a > b ? a : b)).toLocaleString();
}

function App() {
  const [simMeta, setSimMeta] = useState({});
  const [pools, setPools] = useState([]);
  const [logs, setLogs] = useState([]);

  const [selectedSwap, setSelectedSwap] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(Date.now());
  const [secondsAgo, setSecondsAgo] = useState(0);

  const openSwapDetails = (swap) => setSelectedSwap(swap);
  const closeSwapDetails = () => setSelectedSwap(null);

  async function loadAll(silent = false) {
    try {
      const [m, p, l] = await Promise.all([
        fetchSimMeta(),
        fetchPools(),
        fetchSwapLogs(),
      ]);

      setSimMeta(m || {});
      setPools(p || []);
      setLogs(l || []);

      setLastRefresh(Date.now());
      if (!silent) console.log("🔄 Dashboard updated:", new Date().toLocaleTimeString());
    } catch (err) {
      console.error("Dashboard loadAll failed", err);
    }
  }

  // Auto-refresh every 5 seconds
  useEffect(() => {
    loadAll(true);
    const id = setInterval(() => loadAll(true), 5000);
    return () => clearInterval(id);
  }, []);

  // Update "seconds ago" counter
  useEffect(() => {
    const id = setInterval(() => {
      setSecondsAgo(Math.floor((Date.now() - lastRefresh) / 1000));
    }, 1000);
    return () => clearInterval(id);
  }, [lastRefresh]);

  return (
    <div className="App">
      <h1 className="app-title">COLINK Dashboard</h1>

      {/* LIVE section */}
      <div className="global-status" style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <span>
          Data as of: {computeLatestTimestamp(simMeta, pools, logs) || "N/A"}
        </span>

        {/* Live green dot */}
        <span
          style={{
            width: "10px",
            height: "10px",
            background: "#00ff44",
            borderRadius: "50%",
            display: "inline-block",
            boxShadow: "0 0 8px #00ff44",
            animation: "pulseLive 1.5s infinite"
          }}
        ></span>

        {/* Timer */}
        <span style={{ color: "#777", fontSize: "0.9rem" }}>
          (updated {secondsAgo}s ago)
        </span>

        {/* Manual refresh */}
        <button
          onClick={() => loadAll(false)}
          style={{
            padding: "0.3rem 0.8rem",
            background: "#222",
            border: "1px solid #444",
            color: "white",
            borderRadius: "6px",
            cursor: "pointer"
          }}
        >
          Refresh
        </button>
      </div>

      {/* Pools */}
      <section>
        <h2>Pool State</h2>

        {pools.length === 0 ? (
          <p>No pools available.</p>
        ) : (
          pools.map((pool) => (
            <div key={pool.label} className="card">
              <h3>{pool.label}</h3>

              <p><b>Base:</b> {pool.baseSymbol} — {pool.baseLiquidity.toLocaleString()}</p>
              <p><b>Quote:</b> {pool.quoteSymbol} — {pool.quoteLiquidity.toLocaleString()}</p>
              <p><b>LP Supply:</b> {pool.lpTokenSupply.toLocaleString()}</p>
              <p><b>Fee:</b> {pool.feeBps} bps</p>
              <small>Updated: {new Date(pool.lastUpdated).toLocaleString()}</small>
            </div>
          ))
        )}
      </section>

      {/* Swap Logs */}
      <section style={{ marginTop: "2rem" }}>
        <h2>Swap Logs</h2>

        {logs.length === 0 ? (
          <div className="card">
            <b>No swap logs yet</b>
            <p>Run a simulation to generate activity.</p>
          </div>
        ) : (
          <table>
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
                <tr key={idx} onClick={() => openSwapDetails(log)}>
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
      </section>

      {selectedSwap && (
        <SwapDetailsModal swap={selectedSwap} onClose={() => setSelectedSwap(null)} />
      )}
    </div>
  );
}

export default App;