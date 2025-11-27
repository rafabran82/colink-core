import React, { useEffect, useState } from "react";

export default function TVLSpark() {
  const [points, setPoints] = useState([]);

  // Fetch TVL every 5 seconds
  useEffect(() => {
    async function load() {
      try {
        const res = await fetch("http://localhost:5000/api/xrpl/tvl");
        const data = await res.json();
        const tvl = Number(data.tvl) || 0;

        setPoints((prev) => [...prev.slice(-29), tvl]); // keep last 30 points
      } catch (err) {
        console.error("TVL spark error:", err);
      }
    }

    load();
    const timer = setInterval(load, 5000);
    return () => clearInterval(timer);
  }, []);

  if (points.length < 2) return <div style={{ height: "32px" }} />;

  const max = Math.max(...points);
  const min = Math.min(...points);
  const range = max - min || 1;

  const svgPoints = points
    .map((p, i) => {
      const x = (i / (points.length - 1)) * 100;
      const y = 100 - ((p - min) / range) * 100;
      return `${x},${y}`;
    })
    .join(" ");

  const styles = getComputedStyle(document.body);
  const accent = styles.getPropertyValue("--accent")?.trim() || "#4cc2ff";

  return (
    <svg
      width="100%"
      height="32"
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      style={{ display: "block" }}
    >
      <polyline
        fill="none"
        stroke={accent}
        strokeWidth="3"
        points={svgPoints}
        style={{ filter: "drop-shadow(0px 0px 2px rgba(0,0,0,0.5))" }}
      />
    </svg>
  );
}
';
Set-Content -Path $path -Encoding utf8 -Value $code
Write-Host "📈 TVLSpark.jsx created (Apple-style mini sparkline ready)." -ForegroundColor Green
