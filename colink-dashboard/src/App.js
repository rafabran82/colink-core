import React, { useEffect, useState } from "react";
import { fetchSimMeta } from "./api/meta";
import { fetchPools } from "./api/pools";
import { fetchSwapLogs } from "./api/logs";

function App() {
  const [meta, setMeta] = useState(null);
  const [pools, setPools] = useState([]);
  const [swaps, setSwaps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadAll() {
      try {
        setLoading(true);
        setError(null);

        const [m, p, s] = await Promise.all([
          fetchSimMeta(),
          fetchPools(),
          fetchSwapLogs(),
        ]);

        setMeta(m || null);
        setPools(Array.isArray(p) ? p : []);
        setSwaps(Array.isArray(s) ? s : []);
      } catch (err) {
        console.error("Dashboard load failed", err);
        setError("Failed to load data from COLINK API.");
      } finally {
        setLoading(false);
      }
    }

    loadAll();
  }, []);

  return (
    <div style={{ padding: "24px", fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}>
      <h1 style={{ marginBottom: "16px" }}>COLINK Dashboard</h1>

      {loading && <p>Loading data from backend…</p>}
      {error && !loading && (
        <p style={{ color: "red" }}>{error}</p>
      )}

      {/* Meta section */}
      <section style={{ marginTop: "16px", marginBottom: "24px" }}>
        <h2 style={{ fontSize: "18px", marginBottom: "8px" }}>Simulation meta</h2>
        {meta && meta.status ? (
          <ul style={{ marginTop: 0 }}>
            <li>Status: <strong>{meta.status}</strong></li>
            {meta.engine && <li>Engine: {meta.engine}</li>}
            {meta.timestamp && <li>Timestamp: {meta.timestamp}</li>}
          </ul>
        ) : (
          <p>No metadata available.</p>
        )}
      </section>

      {/* Pools section */}
      <section style={{ marginBottom: "24px" }}>
        <h2 style={{ fontSize: "18px", marginBottom: "8px" }}>Pools</h2>
        {pools && pools.length > 0 ? (
          <table style={{ borderCollapse: "collapse", minWidth: "320px" }}>
            <thead>
              <tr>
                <th style={{ borderBottom: "1px solid #ccc", textAlign: "left", padding: "4px 8px" }}>Pair</th>
                <th style={{ borderBottom: "1px solid #ccc", textAlign: "right", padding: "4px 8px" }}>Reserve 1</th>
                <th style={{ borderBottom: "1px solid #ccc", textAlign: "right", padding: "4px 8px" }}>Reserve 2</th>
              </tr>
            </thead>
            <tbody>
              {pools.map((pool, idx) => (
                <tr key={idx}>
                  <td style={{ borderBottom: "1px solid #eee", padding: "4px 8px" }}>{pool.pair}</td>
                  <td style={{ borderBottom: "1px solid #eee", textAlign: "right", padding: "4px 8px" }}>
                    {pool.reserve1}
                  </td>
                  <td style={{ borderBottom: "1px solid #eee", textAlign: "right", padding: "4px 8px" }}>
                    {pool.reserve2}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No pools available.</p>
        )}
      </section>

      {/* Swaps section */}
      <section>
        <h2 style={{ fontSize: "18px", marginBottom: "8px" }}>Recent swaps</h2>
        {swaps && swaps.length > 0 ? (
          <table style={{ borderCollapse: "collapse", minWidth: "360px" }}>
            <thead>
              <tr>
                <th style={{ borderBottom: "1px solid #ccc", textAlign: "left", padding: "4px 8px" }}>Pair</th>
                <th style={{ borderBottom: "1px solid #ccc", textAlign: "right", padding: "4px 8px" }}>Amount in</th>
                <th style={{ borderBottom: "1px solid #ccc", textAlign: "right", padding: "4px 8px" }}>Amount out</th>
                <th style={{ borderBottom: "1px solid #ccc", textAlign: "left", padding: "4px 8px" }}>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {swaps.map((swap, idx) => (
                <tr key={idx}>
                  <td style={{ borderBottom: "1px solid #eee", padding: "4px 8px" }}>{swap.pair}</td>
                  <td style={{ borderBottom: "1px solid #eee", textAlign: "right", padding: "4px 8px" }}>
                    {swap.amount_in}
                  </td>
                  <td style={{ borderBottom: "1px solid #eee", textAlign: "right", padding: "4px 8px" }}>
                    {swap.amount_out}
                  </td>
                  <td style={{ borderBottom: "1px solid #eee", padding: "4px 8px" }}>
                    {swap.timestamp}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No recent swaps.</p>
        )}
      </section>
    </div>
  );
}

export default App;
