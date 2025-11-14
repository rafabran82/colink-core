import React, { useEffect, useState } from "react";
import PoolCard from "../components/PoolCard";
import PoolStatsTable from "../components/PoolStatsTable";
import { fetchPools, PoolState } from "../api/pools";
import { fetchSimMeta } from "../api";

function PoolStatsPage() {
  const [meta, setMeta] = useState(null);
  const [pools, setPools] = useState(/** @type {PoolState[] | null} */ (null));
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
    return () => { cancelled = true; };
  }, []);

  return (
    <div style={{ padding: "24px" }}>
      <h1>Pool Stats</h1>

      {loading && !pools && <p>Loading pool data…</p>}

      {pools && pools.length > 0 && (
        <>
          <PoolCard pools={pools} />
          <div style={{ marginTop: "24px" }}>
            <PoolStatsTable pools={pools} />
          </div>
        </>
      )}
    </div>
  );
}

export default PoolStatsPage;
