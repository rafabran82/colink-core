import React, { useEffect, useState } from "react";
import SwapLogsTable from "../components/SwapLogsTable";
import { fetchSwapLogs, fetchSimMeta } from "../api";

function SwapLogsPage() {
  const [logs, setLogs] = useState([]);
  const [meta, setMeta] = useState(null);
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
    <div style={{ padding: "24px" }}>
      <h1>Recent Swaps</h1>

      {loading && logs.length === 0 && <p>Loading swaps…</p>}
      {logs.length > 0 && <SwapLogsTable logs={logs} />}
    </div>
  );
}

export default SwapLogsPage;
