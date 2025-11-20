import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";

export default function Charts() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const res = await fetch("http://localhost:5000/api/xrpl/tvl");
      const tvl = await res.json();

      const point = {
        time: new Date(tvl.timestamp).toLocaleTimeString(),
        tvl: tvl.tvl
      };

      setData((prev) => [...prev.slice(-20), point]);  // keep last 20 pts
    } catch (err) {
      console.error("Charts fetch error:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const timer = setInterval(load, 5000);
    return () => clearInterval(timer);
  }, []);

  if (loading) {
    return <div className="card">Loading chart...</div>;
  }

  return (
    <div className="card chart-stable-wrapper">
      <h2>XRPL Synthetic TVL Trend</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="tvl" stroke="#3b82f6" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
