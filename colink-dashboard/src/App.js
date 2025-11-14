import React, { useState, useEffect } from "react";
import PoolCard from "./components/PoolCard";
import SwapLogsTable from "./components/SwapLogsTable";

export default function App() {
  const [pools, setPools] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isDark, setIsDark] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  const toggleTheme = () => setIsDark(!isDark);

  // ---------------------------
  // Fetch Pools + Logs Combined
  // ---------------------------
  const refreshAll = async () => {
    try {
      setLoading(true);

      const [poolRes, logRes] = await Promise.all([
        fetch("/api/pools"),
        fetch("/api/swap_logs")
      ]);

      const poolJson = await poolRes.json();
      const logJson = await logRes.json();

      setPools(poolJson);
      setLogs(logJson);

      const now = new Date().toLocaleTimeString();
      setLastUpdated(now);
    } catch (err) {
      console.error("Refresh error:", err);
    } finally {
      setLoading(false);
    }
  };

  // ---------------------------
  // Auto-refresh every 10 seconds
  // ---------------------------
  useEffect(() => {
    refreshAll();                  // Initial load
    const timer = setInterval(refreshAll, 10000);   // 10 seconds
    return () => clearInterval(timer);
  }, []);

  return (
    <div
      style={{
        padding: "24px",
        maxWidth: "1200px",
        margin: "0 auto",
        color: isDark ? "#eee" : "#111",
        backgroundColor: isDark ? "#000" : "#fafafa",
        minHeight: "100vh",
      }}
    >
      {/* Top bar */}
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <h1>
          COLINK Dashboard{" "}
          {loading && (
            <span
              style={{
                marginLeft: "8px",
                fontSize: "0.8rem",
                opacity: 0.7
              }}
            >
              ⏳ refreshing…
            </span>
          )}
        </h1>

        <button
          onClick={toggleTheme}
          style={{
            padding: "6px 14px",
            borderRadius: "999px",
            border: "1px solid #888",
            backgroundColor: isDark ? "#222" : "#f0f0f0",
            color: isDark ? "#f5f5f5" : "#222",
            cursor: "pointer",
            fontSize: "0.85rem",
          }}
        >
          {isDark ? "☀ Light mode" : "🌙 Dark mode"}
        </button>
      </div>

      {/* Global timestamp */}
      {lastUpdated && (
        <div
          style={{
            marginTop: "10px",
            fontSize: "0.8rem",
            opacity: 0.7,
          }}
        >
          Data refreshed at {lastUpdated}
        </div>
      )}

      {/* ---------------- Pool State ---------------- */}
      <section style={{ marginTop: "24px" }}>
        <h2>Pool State</h2>

        {loading && pools.length === 0 && <p>Loading pool state…</p>}

        {!loading && pools.length === 0 && (
          <p>No pool data available.</p>
        )}

        {pools.length > 0 &&
          pools.map((p, i) => <PoolCard key={i} pool={p} />)}
      </section>

      {/* ---------------- Swap Logs ---------------- */}
      <section style={{ marginTop: "24px" }}>
        <h2>Swap Logs</h2>

        {loading && logs.length === 0 && <p>Loading swap logs…</p>}

        {logs.length === 0 && !loading && (
          <div
            style={{
              marginTop: "12px",
              padding: "16px",
              maxWidth: "420px",
              borderRadius: "12px",
              border: "1px solid #444",
              backgroundColor: isDark ? "#111" : "#eee",
              fontSize: "0.9rem",
            }}
          >
            <strong style={{ display: "block", marginBottom: "4px" }}>
              No swap logs yet
            </strong>
            <span style={{ opacity: 0.8 }}>
              Run a simulation or on-ledger test swap to see recent activity.
            </span>
          </div>
        )}

        {logs.length > 0 && <SwapLogsTable logs={logs} />}
      </section>
    </div>
  );
}
