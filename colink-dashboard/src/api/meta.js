export async function fetchSimMeta() {
  const r = await fetch("http://localhost:8000/api/sim/meta");
  if (!r.ok) return null;
  return await r.json();
}

