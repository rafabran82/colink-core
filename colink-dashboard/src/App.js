import React, { useEffect, useState } from "react";
import "./App.css";
import PoolCard from "./components/PoolCard";
import SwapLogsTable from "./components/SwapLogsTable";
import SimMetaBar from "./components/SimMetaBar";
import { fetchPoolState, fetchSwapLogs, fetchSimMeta } from "./api";

function App() {
  const [pool, setPool] = useState(null);
  const [logs, setLogs] = useState([]);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [m, p, s] = await Promise.all([
          fetchSimMeta(),
          fetchPoolState(),
          fetchSwapLogs(),
        ]);

        if (!cancelled) {
          setMeta(m);
          setPool(p);
          setLogs(s);
          setLoading(false);
        }
      } catch (err) {
        console.error("Dashboard load failed", err);
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => (cancelled = true);
  }, []);

  return (
    <div
      style={{
        padding: "24px",
        fontFamily:
          "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
      }}
    >
      <SimMetaBar meta={meta} />

      <h1>COLINK Dashboard</h1>

      <section style={{ marginTop: "16px" }}>
        <h2>Pool State</h2>
        {loading && !pool && <p>Loading pool state…</p>}
        {pool && <PoolCard pool={pool} />}
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
