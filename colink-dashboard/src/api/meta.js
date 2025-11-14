const API_BASE = "http://localhost:5001";

/**
 * Fetch simulation metadata from backend
 * Returns {} if backend unavailable
 */
export async function fetchSimMeta() {
  try {
    const res = await fetch(`${API_BASE}/meta`);
    if (!res.ok) {
      console.error("fetchSimMeta: backend returned", res.status);
      return {};
    }
    const data = await res.json();
    console.log("fetchSimMeta received:", data);
    return data || {};
  } catch (err) {
    console.error("fetchSimMeta error:", err);
    return {};
  }
}
