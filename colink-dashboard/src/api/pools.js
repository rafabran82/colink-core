import axios from "axios";

export async function fetchPools() {
  const res = await axios.get("http://127.0.0.1:8000/api/pools/state");
  return res.data;
}
