import React, { useState, useEffect } from "react";
import "./App.css";

import { fetchPools } from "./api/pools";
import { fetchSimMeta, fetchSwapLogs } from "./api";

import PoolCard from "./components/PoolCard";
import SwapLogsTable from "./components/SwapLogsTable";
import SimMetaBar from "./components/SimMetaBar";

function App() {
  const [theme, setTheme] = useState(() => {
    const saved = window.localStorage.getItem("colink-theme");
    return saved === "dark" || saved === "light" ? saved : "light";
  });

  const isDark = theme === "dark";

  const [pools, setPools] = useState([]);
  const [logs, setLogs] = useState([]);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    window.localStorage.setItem("colink-theme", theme);
    if (theme === "dark") document.body.classList.add("dark");
    else document.body.classList.remove("dark");
  }, [theme]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        console.log("🔵 fetchPools() starting"); const [poolList, swapLogs, simMeta] = await Promise.all([
          fetchPools(),
          fetchSwapLogs(),
          fetchSimMeta(),
        ]);

        if (!cancelled) {
          console.log("🟢 fetched pools:", poolList); setPools(poolList || []);
          setLogs(swapLogs || []);
          setMeta(simMeta || null);
          setLoading(false);
        }
      } catch (err) {
        console.error("Dashboard load failed", err);
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return (<div style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>) => { cancelled = true; };
  }, []);

  function toggleTheme() {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  }

  return (<div style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "16px",
        }}
      >
        <SimMetaBar meta={meta} />

        <button
          onClick={toggleTheme}
          style={{
            padding: "6px 12px",
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

      <h1>COLINK Dashboard</h1>

      <section style={{ marginTop: "16px" }}>
                <h2>Pool State</h2>

        {/* Loading indicator */}
        {loading && pools.length === 0 && <p>Loading pool state…</p>}

        {/* No pools */}
        {!loading && pools.length === 0 && (
          <p>No pool data available.</p>
        )}

        {/* Render all pools */}
        {!loading && pools.length > 0 && pools.map((p, i) => (
          <PoolCard key={i} pool={p} />
        ))}
      </section>

      <section style={{ marginTop: "24px" }}>
        <h2>Swap Logs</h2>
        {loading && logs.length === 0 && <p>Loading swap logs…</p>}
        {logs.length > 0 && <SwapLogsTable logs={logs} />}
      </section>
    </div>
  );
}

export default App;





