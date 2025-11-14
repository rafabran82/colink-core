import React, { useEffect, useState } from "react";
import PoolCard from "./components/PoolCard";
import SwapLogsTable from "./components/SwapLogsTable";

export default function App() {
  const [isDark, setIsDark] = useState(true);
  const [pools, setPools] = useState([]);
  const [logs, setLogs] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [flash, setFlash] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchAll = async () => {
    try {
      setLoading(true);

      const [metaRes, poolsRes, logsRes] = await Promise.all([
        fetch("http://127.0.0.1:8000/api/sim/meta").then(r => r.json()),
        fetch("http://127.0.0.1:8000/api/pools/state").then(r => r.json()),
        fetch("http://127.0.0.1:8000/api/swaps/recent").then(r => r.json())
      ]);

      if (poolsRes) setPools(poolsRes);
      if (logsRes) setLogs(logsRes);

      const metaTime = metaRes?.lastUpdated || null;
      setLastUpdated(metaTime);

      setFlash(true);
      setTimeout(() => setFlash(false), 1200);
    } catch (err) {
      console.error("Dashboard fetchAll error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div
      style={{
        padding: "24px",
        maxWidth: "1200px",
        margin: "0 auto",
        color: isDark ? "#f5f5f5" : "#222",
        backgroundColor: isDark ? "#000" : "#fff",
        minHeight: "100vh",
        transition: "background 0.3s ease, color 0.3s ease"
      }}
    >

      {/* Theme Toggle */}
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button
          onClick={() => setIsDark(!isDark)}
          style={{
            padding: "6px 14px",
            borderRadius: "999px",
            border: "1px solid #888",
            backgroundColor: isDark ? "#222" : "#f0f0f0",
            color: isDark ? "#f5f5f5" : "#222",
            cursor: "pointer",
            fontSize: "0.85rem"
          }}
        >
          {isDark ? "☀ Light mode" : "🌙 Dark mode"}
        </button>
      </div>

      <h1 style={{ fontSize: "2.2rem", marginTop: "12px" }}>COLINK Dashboard</h1>

      {/* Global updated timestamp */}
      {lastUpdated && (
        <div
          style={{
            marginTop: "8px",
            fontSize: "0.9rem",
            opacity: 0.7
          }}
        >
          Data as of {new Date(lastUpdated).toLocaleString()}
        </div>
      )}

      {/* Flash Highlight Bar */}
      <div
        style={{
          height: "4px",
          marginTop: "8px",
          backgroundColor: flash ? "rgba(0,150,255,0.35)" : "transparent",
          transition: "background-color 1.2s ease-out"
        }}
      ></div>

      {/* ================= Pool State ================= */}
      <section style={{ marginTop: "28px" }}>
        <h2>Pool State</h2>

        {loading && pools.length === 0 && (
          <p>Loading pool data…</p>
        )}

        {!loading && pools.length === 0 && (
          <p>No pool data available.</p>
        )}

        {pools.length > 0 &&
          pools.map((p, i) => <PoolCard key={i} pool={p} />)}
      </section>

      {/* ================= Swap Logs ================= */}
      <section style={{ marginTop: "36px" }}>
        <h2>Swap Logs</h2>

        {loading && logs.length === 0 && <p>Loading swap logs…</p>}

        {logs.length === 0 && !loading && (
          <div
            style={{
              marginTop: "12px",
              padding: "16px",
              borderRadius: "12px",
              backgroundColor: isDark ? "#111" : "#eee",
              border: isDark ? "1px solid #444" : "1px solid #ccc",
              maxWidth: "420px"
            }}
          >
            <strong style={{ display: "block", marginBottom: "6px" }}>
              No swap logs yet
            </strong>
            <span style={{ fontSize: "0.9rem", opacity: 0.8 }}>
              Run a simulation or on-ledger test swap to see recent activity.
            </span>
          </div>
        )}

        {logs.length > 0 && (
          <SwapLogsTable logs={logs} />
        )}
      </section>
    </div>
  );
}
