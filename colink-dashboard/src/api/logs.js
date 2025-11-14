import axios from "axios";

export async function fetchSwapLogs() {
  try {
    const res = await axios.get("http://127.0.0.1:8000/api/swaps/recent");
    return res.data;
  } catch (err) {
    console.error("fetchSwapLogs failed", err);
    return [];
  }
}
