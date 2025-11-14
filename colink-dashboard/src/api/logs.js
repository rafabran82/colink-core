const API_BASE = "http://localhost:5001";

/**
 * Fetch swap logs from backend
 * Returns [] if backend unavailable
 */
export async function fetchSwapLogs() {
  try {
    const res = await fetch(`${API_BASE}/logs`);
    if (!res.ok) {
      console.error("fetchSwapLogs: backend returned", res.status);
      return [];
    }
    const data = await res.json();
    console.log("fetchSwapLogs received:", data);
    return data.logs || [];
  } catch (err) {
    console.error("fetchSwapLogs error:", err);
    return [];
  }
}
