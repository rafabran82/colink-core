import React, { useEffect, useState } from "react";
import "./App.css";
import PoolCard from "./components/PoolCard";
import SwapLogsTable from "./components/SwapLogsTable";
import SimMetaBar from "./components/SimMetaBar";

import { fetchPools } from "./api/pools";
import { fetchSwapLogs, fetchSimMeta } from "./api";

function App() {
  const [theme, setTheme] = useState(() => {
    if (typeof window === "undefined") return "light";
    const saved = window.localStorage.getItem("colink-theme");
    return saved === "dark" || saved === "light" ? saved : "light";
  });

  const isDark = theme === "dark";
  const [pools, setPools] = useState([]);
  const [logs, setLogs] = useState([]);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("colink-theme", theme);
    }
  }, [theme]);

  useEffect(() => {
    if (theme === "dark") document.body.classList.add("dark");
    else document.body.classList.remove("dark");
  }, [theme]);

  // Load dashboard data
  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [m, p, s] = await Promise.all([
          fetchSimMeta(),
          fetchPools(),
          fetchSwapLogs(),
        ]);

        if (!cancelled) {
          setMeta(m);
          setPools(p);
          setLogs(s);
          setLoading(false);
        }
      } catch (err) {
        console.error("Dashboard load failed", err);
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  return (
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
          onClick={() => setTheme((prev) => (prev === "light" ? "dark" : "light"))}
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
        {loading && pools.length === 0 && <p>Loading pool state…</p>}
        {pools.length > 0 && pools.map((pool, i) => (
          <PoolCard key={i} pool={pool} />
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
