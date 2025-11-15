import React, { useEffect, useState } from "react";
import { fetchSwapLogs } from "../api/pools";
import SwapLogsTable from "../components/SwapLogsTable";

function SwapLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const list = await fetchSwapLogs();
        setLogs(list);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h1>Swap Logs</h1>

      {loading && logs.length === 0 && <p>Loading swap logsâ€¦</p>}

      {!loading && logs.length === 0 && (
        <p>No swap logs available.</p>
      )}

      {logs.length > 0 && (
        <SwapLogsTable logs={logs} />
      )}
    </div>
  );
}

export default SwapLogsPage;

