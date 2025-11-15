import axios from "axios";

const BASE_URL = "http://127.0.0.1:8000/api";

export async function fetchSwapLogs() {
  try {
    const res = await axios.get(BASE_URL + "/swaps/recent");
    if (!res || typeof res.data === "undefined") {
      console.error("fetchSwapLogs: empty response");
      return [];
    }
    return res.data || [];
  } catch (err) {
    console.error("fetchSwapLogs failed", err);
    return [];
  }
}

