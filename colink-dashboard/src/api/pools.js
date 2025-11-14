import axios from "axios";

const BASE_URL = "http://127.0.0.1:8000/api";

export async function fetchPools() {
  try {
    const res = await axios.get(BASE_URL + "/pools/state");
    if (!res || typeof res.data === "undefined") {
      console.error("fetchPools: empty response");
      return [];
    }
    return res.data || [];
  } catch (err) {
    console.error("fetchPools failed", err);
    return [];
  }
}
