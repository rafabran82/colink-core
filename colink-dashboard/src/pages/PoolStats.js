import React, { useEffect, useState } from "react";
import PoolCard from "../components/PoolCard";
import PoolStatsTable from "../components/PoolStatsTable";
import { fetchPools, fetchSimMeta } from "../api/pools";

function PoolStatsPage() {
  const [pools, setPools] = useState([]);
  const [meta, setMeta] = useState(null);
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
    <div style={{ padding: "24px" }}>
      <h1>Pool Statistics</h1>

      {loading && pools.length === 0 && <p>Loading pools…</p>}

      {/* Overview table */}
      {pools.length > 0 && <PoolStatsTable pools={pools} />}

      {/* Each individual pool card */}
      <div style={{ marginTop: "24px" }}>
        {pools.map((p, i) => (
          <PoolCard key={i} pool={p} />
        ))}
      </div>
    </div>
  );
}

export default PoolStatsPage;

