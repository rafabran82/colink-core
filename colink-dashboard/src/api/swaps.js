export async function fetchSwaps() {
  const r = await fetch("http://localhost:8000/api/sim/swaps");
  if (!r.ok) return [];
  return await r.json();
}

