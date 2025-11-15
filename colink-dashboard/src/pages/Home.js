import React, { useEffect, useState } from "react";
import PoolCard from "../components/PoolCard";
import { fetchPools } from "../api/pools";
import { fetchSimMeta } from "../api";

function Home() {
  const [meta, setMeta] = useState(null);
  const [pools, setPools] = useState([]);
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

  const renderAmmDemo = () => {
    if (!meta || !meta.amm_demo) return null;

    const { png, json, ndjson } = meta.amm_demo;

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
          src={`/${png}`}
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
          <a href={`/${png}`} target="_blank" rel="noopener noreferrer">PNG</a>
          <a href={`/${json}`} target="_blank" rel="noopener noreferrer">JSON</a>
          <a href={`/${ndjson}`} target="_blank" rel="noopener noreferrer">NDJSON</a>
        </div>
      </div>
    );
  };

  return (
    <div style={{ padding: "24px" }}>
      <h1>COLINK Dashboard - Overview</h1>

      {renderAmmDemo()}

      {loading && pools.length === 0 && <p>Loading pools…</p>}

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
