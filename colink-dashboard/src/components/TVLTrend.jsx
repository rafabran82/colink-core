import React from "react";
import {
  LineChart, Line,
  XAxis, YAxis,
  Tooltip, ResponsiveContainer, CartesianGrid
} from "recharts";

export default function TVLTrend({ data }) {
  // Read theme variables from CSS
  const styles = getComputedStyle(document.body);

  const textColor = styles.getPropertyValue("--text-primary")?.trim() || "#ffffff";
  const gridColor = styles.getPropertyValue("--text-secondary")?.trim() || "#555";
  const accentColor = styles.getPropertyValue("--accent")?.trim() || "#4cc2ff";

  return (
    <div style={{ width: "100%", height: 320 }}>
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid stroke={gridColor} strokeDasharray="3 3" />

          <XAxis
            dataKey="time"
            stroke={textColor}
            tick={{ fill: textColor }}
          />

          <YAxis
            stroke={textColor}
            tick={{ fill: textColor }}
          />

          <Tooltip
            contentStyle={{
              background: "var(--card-bg)",
              border: "1px solid var(--text-secondary)",
              borderRadius: "8px",
              color: "var(--text-primary)"
            }}
          />

          <Line
            type="monotone"
            dataKey="value"
            stroke={accentColor}
            strokeWidth={3}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

