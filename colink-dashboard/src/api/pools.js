export async function fetchPools() {
  const r = await fetch("http://localhost:8000/api/sim/pools");
  if (!r.ok) return [];
  return await r.json();
}

