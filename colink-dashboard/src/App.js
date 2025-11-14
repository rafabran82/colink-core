import React, { useEffect, useState } from "react";
import "./App.css";

import { fetchSimMeta } from "./api/meta";
import { fetchPools } from "./api/pools";
import { fetchSwapLogs } from "./api/logs";
import SwapDetailsModal from "./components/SwapDetailsModal";
import PoolChart from "./components/PoolChart";
import SwapVolumeChart from "./components/SwapVolumeChart";
import { connectWS } from "./api/ws";

function computeLatestTimestamp(meta, pools, swaps) {
  const ts = [];
  if (meta?.lastUpdated) ts.push(new Date(meta.lastUpdated));
  if (Array.isArray(pools))
    pools.forEach(p => p.lastUpdated && ts.push(new Date(p.lastUpdated)));
  if (Array.isArray(swaps))
    swaps.forEach(s => {
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

  // === Chart histories ===
  const [poolHistory, setPoolHistory] = useState({});
  const [swapVolume, setSwapVolume] = useState([]);

  const openSwapDetails = (swap) => setSelectedSwap(swap);
  const closeSwapDetails = () => setSelectedSwap(null);

  // Add a history point for each pool on update
  const recordPools = (poolsList) => {
    const now = Date.now();
    const updated = { ...poolHistory };
    poolsList.forEach(p => {
      if (!updated[p.label]) updated[p.label] = [];
      updated[p.label].push({
        t: now,
        base: p.baseLiquidity || 0,
        quote: p.quoteLiquidity || 0
      });
      updated[p.label] = updated[p.label].slice(-80);
    });
    setPoolHistory(updated);
  };

  // Add swap volume point
  const recordSwap = (swap) => {
    const now = Date.now();
    const amount = parseFloat(swap.amountIn || 0);
    const updated = [...swapVolume];
    updated.push({ t: now, vol: amount });
    setSwapVolume(updated.slice(-50));
  };

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

      recordPools(p || []);
      l.forEach(recordSwap);

      setLastRefresh(Date.now());
    } catch (err) {
      console.error("Dashboard loadAll failed", err);
    }
  }

  useEffect(() => {
    loadAll(true);
    const id = setInterval(() => loadAll(true), 5000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const id = setInterval(() => {
      setSecondsAgo(Math.floor((Date.now() - lastRefresh) / 1000));
    }, 1000);
    return () => clearInterval(id);
  }, [lastRefresh]);

  // === WebSocket ===
  useEffect(() => {
    connectWS((msg) => {
      if (msg.type === "swap") {
        msg.data.__flash = true;
        setLogs(prev => {
          const updated = [msg.data, ...prev];
          return updated;
        });
        recordSwap(msg.data);
        setLastRefresh(Date.now());
      }

      if (msg.type === "pool_update") {
        setPools(prev => {
          const updated = prev.map(p =>
            p.label === msg.data.label
              ? { ...p, ...msg.data, __flash: true }
              : p
          );
          recordPools(updated);
          return updated;
        });
        setLastRefresh(Date.now());
      }

      if (msg.type === "meta") {
        setSimMeta(prev => ({ ...prev, ...msg.data }));
        setLastRefresh(Date.now());
      }
    });
  }, []);

  return (
    <div className="App">
      <h1 className="app-title">COLINK Dashboard</h1>

      <div className="global-status">
        Data as of: {computeLatestTimestamp(simMeta, pools, logs) || "N/A"}
        <span className="live-dot"></span>
        <span style={{ color: "#888" }}>({secondsAgo}s ago)</span>
      </div>

      {/* Pool charts */}
      <h2>Liquidity Charts</h2>
      {Object.keys(poolHistory).map(label => (
        <div key={label} className="chart-card">
          <PoolChart label={label} data={poolHistory[label]} />
        </div>
      ))}

      {/* Swap volume */}
      <h2>Swap Volume</h2>
      <div className="chart-card">
        <SwapVolumeChart data={swapVolume} />
      </div>

      {/* Pools */}
      <h2>Pool State</h2>
      {pools.map(pool => (
        <div
          key={pool.label}
          className={`card ${pool.__flash ? "flash" : ""}`}
        >
          <h3>{pool.label}</h3>
          <p><b>Base:</b> {pool.baseSymbol} — {pool.baseLiquidity}</p>
          <p><b>Quote:</b> {pool.quoteSymbol} — {pool.quoteLiquidity}</p>
          <p><b>LP Supply:</b> {pool.lpTokenSupply}</p>
        </div>
      ))}

      {/* Logs */}
      <h2>Swap Logs</h2>
      <table>
        <tbody>
          {logs.map((log, idx) => (
            <tr
              key={idx}
              className={log.__flash ? "flash" : ""}
              onClick={() => setSelectedSwap(log)}
            >
              <td>{log.id}</td>
              <td>{log.pool}</td>
              <td>{log.amountIn}</td>
              <td>{log.amountOut}</td>
              <td>{new Date(log.timestamp).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {selectedSwap && (
        <SwapDetailsModal swap={selectedSwap} onClose={closeSwapDetails} />
      )}
    </div>
  );
}

export default App;