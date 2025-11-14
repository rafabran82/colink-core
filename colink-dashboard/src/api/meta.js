import axios from "axios";

const BASE_URL = "http://127.0.0.1:8000/api";

export async function fetchSimMeta() {
  try {
    const res = await axios.get(BASE_URL + "/sim/meta");
    if (!res || typeof res.data === "undefined") {
      console.error("fetchSimMeta: empty response");
      return {};
    }
    return res.data || {};
  } catch (err) {
    console.error("fetchSimMeta failed", err);
    return {};
  }
}
