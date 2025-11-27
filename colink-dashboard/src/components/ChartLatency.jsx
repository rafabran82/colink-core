import React, { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import "chart.js/auto";

export default function ChartLatency() {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    async function measure() {
      try {
        const start = performance.now();
        const res = await fetch("http://localhost:5000/api/xrpl/tvl");
        await res.json();
        const end = performance.now();

        const latency = end - start;

        const point = {
          time: new Date().toLocaleTimeString(),
          value: Number(latency.toFixed(1))
        };

        setHistory((prev) => [...prev.slice(-20), point]);
      } catch (err) {
        console.error("Latency chart error:", err);
      }
    }

    measure();
    const interval = setInterval(measure, 5000);
    return () => clearInterval(interval);
  }, []);

  const chartData = {
    labels: history.map((p) => p.time),
    datasets: [
      {
        label: "API Latency (ms)",
        data: history.map((p) => p.value),
        borderColor: "#f472b6",
        borderWidth: 3,
        tension: 0.25,
        pointRadius: 1
      }
    ]
  };

  const options = {
    scales: {
      x: { ticks: { color: "var(--text-color)" } },
      y: { ticks: { color: "var(--text-color)" } }
    },
    plugins: {
      legend: { labels: { color: "var(--text-color)" } }
    },
    responsive: true,
    maintainAspectRatio: false
  };

  return (
    <div className="card chart-card">
      <h2 className="card-title">XRPL API Latency</h2>
      <div style={{ height: "240px" }}>
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}
