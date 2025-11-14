import React, { useEffect, useState } from "react";
import "../App.css";
import SimMetaBar from "../components/SimMetaBar";
import PoolCard from "../components/PoolCard";
import { fetchPoolState, fetchSimMeta } from "../api";

function PoolStatsPage() {
  const [meta, setMeta] = useState(null);
  const [pool, setPool] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [m, p] = await Promise.all([
          fetchSimMeta(),
          fetchPoolState(),
        ]);

        if (!cancelled) {
          setMeta(m);
          setPool(p);
          setLoading(false);
        }
      } catch (err) {
        console.error("PoolStatsPage load failed", err);
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

      <h1>COLINK Pool Stats</h1>

      <section style={{ marginTop: "16px" }}>
        <h2>Pool State</h2>
        {loading && !pool && <p>Loading pool state…</p>}
        {pool && <PoolCard pool={pool} />}
      </section>
    </div>
  );
}

export default PoolStatsPage;
