import React, { useEffect, useState } from "react";
import "./App.css";

import { fetchSimMeta } from "./api/meta";
import { fetchPools } from "./api/pools";
import { fetchSwapLogs } from "./api/logs";
import SwapDetailsModal from "./components/SwapDetailsModal";

function computeLatestTimestamp(simMeta, pools, swaps) {
  const ts = [];

  if (simMeta?.lastUpdated) ts.push(new Date(simMeta.lastUpdated));

  if (Array.isArray(pools))
    pools.forEach((p) => p.lastUpdated && ts.push(new Date(p.lastUpdated)));

  if (Array.isArray(swaps))
    swaps.forEach((s) => {
      const t = s.timestamp || s.executed_at;
      if (t) ts.push(new Date(t));
    });

  if (ts.length === 0) return "N/A";
  const latest = ts.reduce((a, b) => (a > b ? a : b));
  return latest.toLocaleString();
}

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

function App() {
  const [simMeta, setSimMeta] = useState({});
  const [pools, setPools] = useState([]);
  const [logs, setLogs] = useState([]);

  const [selectedSwap, setSelectedSwap] = useState(null);

  const openSwapDetails = (swap) => setSelectedSwap(swap);
  const closeSwapDetails = () => setSelectedSwap(null);

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
    <div className="App">
      <h1 className="app-title">COLINK Dashboard</h1>

      <div className="global-status">
        Data as of: {computeLatestTimestamp(simMeta, pools, logs)}
      </div>

      {/* ------------ POOLS ------------- */}
      <section>
        <h2>Pool State</h2>

        {pools.length === 0 ? (
          <p>No pools available.</p>
        ) : (
          pools.map((pool) => (
            <div key={pool.label} className={`card ${pool.__flash ? "flash" : ""}`}>
              <h3>{pool.label}</h3>

              <p><b>Base:</b> {pool.baseSymbol} — {pool.baseLiquidity.toLocaleString()}</p>
              <p><b>Quote:</b> {pool.quoteSymbol} — {pool.quoteLiquidity.toLocaleString()}</p>
              <p><b>LP Supply:</b> {pool.lpTokenSupply.toLocaleString()}</p>
              <p><b>Fee:</b> {pool.feeBps} bps</p>

              <p>
                <small>
                  Updated: {new Date(pool.lastUpdated).toLocaleString()}
                </small>
              </p>
            </div>
          ))
        )}
      </section>

      {/* ------------ SWAP LOGS ------------- */}
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
                <tr
                  key={idx}
                  onClick={() => openSwapDetails(log)}
                  className={log.__flash ? "flash" : ""}
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
      </section>

      {selectedSwap && (
        <SwapDetailsModal swap={selectedSwap} onClose={closeSwapDetails} />
      )}
    </div>
  );
}

export default App;