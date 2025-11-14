import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer
} from "recharts";

export default function PoolChart({ data = [], label }) {
  if (!Array.isArray(data) || data.length === 0)
    return <div style={{ color: "#888" }}>No chart data.</div>;

  return (
    <div style={{ width: "100%", height: "260px" }}>
      <h4>{label} Liquidity Trend</h4>
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid stroke="#222" />
          <XAxis dataKey="t" hide />
          <YAxis stroke="#999" />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="base"
            stroke="#00eaff"
            strokeWidth={2}
            dot={false}
            isAnimationActive={true}
          />
          <Line
            type="monotone"
            dataKey="quote"
            stroke="#ff00dd"
            strokeWidth={2}
            dot={false}
            isAnimationActive={true}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}