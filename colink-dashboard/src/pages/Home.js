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

  return (
    <div style={{ padding: "24px" }}>
      <h1>COLINK Dashboard — Overview</h1>

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
