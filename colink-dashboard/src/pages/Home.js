import React, { useEffect, useState } from "react";
import PoolCard from "../components/PoolCard";
import { fetchPools } from "../api/pools";`r`nimport { fetchSwaps } from "../api/swaps";
import { fetchSimMeta } from "../api";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import React, { useEffect, useState } from "react";

function AMMGraph() {
  const [data, setData] = useState([]);

  const fetchData = async () => {
    const response = await fetch("http://localhost:8000/api/sim/meta");
    const data = await response.json();
    setData(data);
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="price" stroke="#8884d8" />
      </LineChart>
    </ResponsiveContainer>
  );
}

export default AMMGraph; {
  const [meta, setMeta] = useState(null);
  const [pools, setPools]\r\n  const [swaps, setSwaps] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [m, p] = await Promise.all([
          fetchSimMeta(),
          fetchPools(),
        ]);

        if (!cancelled) {
          setMeta(m);
          setPools(p);
          setLoading(false);
        }
      } catch (err) {
        console.error("Home load failed", err);
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  // -------------------------
  // AMM DEMO PANEL COMPONENT
  // -------------------------
  const renderAmmDemo = () => {
    if (!meta || !meta.amm_demo) return null;

    const { png, json, ndjson } = meta.amm_demo;

    // Prefix with backend API origin
    const base = "http://localhost:8000";

    return (
      <div style={{
        marginTop: "16px",
        marginBottom: "24px",
        padding: "16px",
        border: "1px solid #ddd",
        borderRadius: "8px",
        background: "#fafafa"
      }}>
        <h2>AMM Demo Output</h2>

        <p style={{ marginBottom: "12px", color: "#444" }}>
          Generated from the latest Local CI run.
        </p>

        <img
          src={`${base}/${png}`}
          alt="AMM Demo"
          style={{
            width: "100%",
            maxWidth: "480px",
            borderRadius: "6px",
            border: "1px solid #ccc",
            marginBottom: "12px"
          }}
        />

        <div style={{ display: "flex", gap: "12px" }}>
          <a href={`${base}/${png}`} target="_blank" rel="noopener noreferrer">PNG</a>
          <a href={`${base}/${json}`} target="_blank" rel="noopener noreferrer">JSON</a>
          <a href={`${base}/${ndjson}`} target="_blank" rel="noopener noreferrer">NDJSON</a>
        </div>
      </div>
    );
  };

  return (
    <div style={{ padding: "24px" }}>
      <h1>COLINK Dashboard - Overview</h1>

      {/* AMM DEMO PANEL */}
      {renderAmmDemo()}

      {loading && pools.length === 0 && <p>Loading poolsâ€¦</p>}

      {pools.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {pools.map((p, i) => (
            <PoolCard key={i} pool={p} />
          ))}
        </div>
      )}
    </div>
  );
}

export default Home;

      <h3>Recent swaps</h3>
      {swaps.length === 0 && <p>No recent swaps.</p>}
      {swaps.length > 0 && (
        <table>
          <thead><tr><th>Pair</th><th>Amount in</th><th>Amount out</th><th>Timestamp</th></tr></thead>
          <tbody>
            {swaps.map((s, i) => (
              <tr key={i}>
                <td>{s.pair}</td>
                <td>{s.amount_in}</td>
                <td>{s.amount_out}</td>
                <td>{s.timestamp}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}


