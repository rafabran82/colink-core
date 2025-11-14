import React, { useEffect, useState } from "react";
import "../App.css";
import SimMetaBar from "../components/SimMetaBar";
import SwapLogsTable from "../components/SwapLogsTable";
import { fetchSwapLogs, fetchSimMeta } from "../api";

function SwapLogsPage() {
  const [meta, setMeta] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [m, s] = await Promise.all([
          fetchSimMeta(),
          fetchSwapLogs(),
        ]);

        if (!cancelled) {
          setMeta(m);
          setLogs(s);
          setLoading(false);
        }
      } catch (err) {
        console.error("SwapLogsPage load failed", err);
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div
      style={{
        padding: "24px",
        minHeight: "100vh",
        backgroundColor: "var(--bg)",
        color: "var(--text)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "16px",
        }}
      >
        <SimMetaBar meta={meta} />
      </div>

      <h1>COLINK Swap Logs</h1>

      <section style={{ marginTop: "16px" }}>
        <h2>Recent Swaps</h2>
        {loading && logs.length === 0 && <p>Loading swap logs…</p>}
        {logs.length > 0 && <SwapLogsTable logs={logs} />}
      </section>
    </div>
  );
}

export default SwapLogsPage;
