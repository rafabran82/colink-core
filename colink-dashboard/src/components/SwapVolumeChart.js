import React from "react";
import {
  AreaChart,
  Area,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  XAxis,
  YAxis
} from "recharts";

export default function SwapVolumeChart({ data = [] }) {
  if (!Array.isArray(data) || data.length === 0)
    return <div style={{ color: "#888" }}>No swap volume yet.</div>;

  return (
    <div style={{ width: "100%", height: "240px" }}>
      <h4>Swap Volume (last 50 swaps)</h4>
      <ResponsiveContainer>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorVol" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00ff99" stopOpacity={0.9} />
              <stop offset="95%" stopColor="#00ff99" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#222" />
          <XAxis dataKey="t" hide />
          <YAxis stroke="#999" />
          <Tooltip />
          <Area
            type="monotone"
            dataKey="vol"
            stroke="#00ff99"
            fill="url(#colorVol)"
            strokeWidth={2}
            isAnimationActive={true}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}