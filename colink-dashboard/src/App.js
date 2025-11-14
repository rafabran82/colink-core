import React, { useEffect, useState } from "react";
import "./App.css";
import PoolCard from "./components/PoolCard";
import SwapLogsTable from "./components/SwapLogsTable";
import SimMetaBar from "./components/SimMetaBar";
import { fetchSimMeta, fetchSwapLogs } from "./api";
import { fetchPools } from "./api/pools";

function App() {
  // Theme with localStorage persistence
  const [theme, setTheme] = useState(() => {
    if (typeof window === "undefined") {
      return "light";
    }
    const saved = window.localStorage.getItem("colink-theme");
    if (saved === "dark" || saved === "light") {
      return saved;
    }
    return "light";
  });

  const isDark = theme === "dark";

  const [pools, setPools] = useState([]);
  const [logs, setLogs] = useState([]);
  const [meta, setMeta] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading] = useState(true);

  // Persist theme
  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("colink-theme", theme);
    }
  }, [theme]);

  // Apply class to body for CSS theme (handled in index.css / App.css)
  useEffect(() => {
    if (typeof document === "undefined") return;
    if (isDark) {
      document.body.classList.add("dark");
    } else {
      document.body.classList.remove("dark");
    }
  }, [isDark]);

  // Load dashboard data
  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        console.log("fetchPools() starting");
        const [poolList, swapLogs, simMeta] = await Promise.all([
          fetchPools(),
          fetchSwapLogs(),
          fetchSimMeta(),
        ]);
        console.log("fetched pools:", poolList);

        if (cancelled) {
          return;
        }

        setPools(Array.isArray(poolList) ? poolList : []);
        setLogs(Array.isArray(swapLogs) ? swapLogs : []);
        setMeta(simMeta || null);
      } catch (err) {
        console.error("Dashboard load failed", err);
        if (!cancelled) {
          setPools([]);
          setLogs([]);
          setMeta(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  function toggleTheme() {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  }

  return (
    <div
      style={{
        padding: "24px",
        minHeight: "100vh",
      }}
    >
      {/* Top bar: theme toggle + meta */}
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
      {lastUpdated && (
        <p
          style={{
            marginTop: "4px",
            fontSize: "0.8rem",
            opacity: 0.7,
          }}
        >
          Data as of {lastUpdated.toLocaleString()}
        </p>
      )}

      {/* Pool State Section */}
      <section style={{ marginTop: "16px" }}>
        <h2>Pool State</h2>

        {loading && pools.length === 0 && <p>Loading pool state…</p>}

        {!loading && pools.length === 0 && (
          <p>No pool data available.</p>
        )}

        {pools.length > 0 &&
          pools.map((pool, i) => <PoolCard key={i} pool={pool} />)}
      </section>

      {/* Swap Logs Section */}
      <section style={{ marginTop: "24px" }}>
        <h2>Swap Logs</h2>

        {loading && logs.length === 0 && <p>Loading swap logs…</p>}

        {!loading && logs.length === 0 && (
          (
  <div
    style={{
      marginTop: "12px",
      padding: "16px 20px",
      maxWidth: "420px",
      borderRadius: "12px",
      border: "1px solid #444",
      backgroundColor: isDark ? "#111" : "#fafafa",
      color: isDark ? "#ddd" : "#333",
      fontSize: "0.9rem",
    }}
  >
    <strong style={{ display: "block", marginBottom: "4px" }}>
      No swap logs yet
    </strong>
    <span style={{ opacity: 0.8 }}>
      Run a simulation or on-ledger test swap to see recent activity here.
    </span>
  </div>
)
        )}

        {logs.length > 0 && <SwapLogsTable logs={logs} />}
      </section>
    </div>
  );
}

export default App;


