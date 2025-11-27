import React, { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import "chart.js/auto";

export default function ChartXrpPrice() {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch("http://localhost:5000/api/xrpl/tvl");
        const data = await res.json();

        const point = {
          time: new Date().toLocaleTimeString(),
          value: data.tvl || 0,
        };

        setHistory((prev) => [...prev.slice(-20), point]);
      } catch (err) {
        console.error("Chart error:", err);
      }
    }

    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  const chartData = {
    labels: history.map((p) => p.time),
    datasets: [
      {
        label: "Synthetic TVL",
        data: history.map((p) => p.value),
        borderColor: "#00eaff",
        borderWidth: 3,
        tension: 0.25,
        pointRadius: 1,
      },
    ],
  };

  const options = {
    scales: {
      x: { ticks: { color: "var(--text-color)" } },
      y: { ticks: { color: "var(--text-color)" } },
    },
    plugins: {
      legend: { labels: { color: "var(--text-color)" } },
    },
    responsive: true,
    maintainAspectRatio: false,
  };

  return (
    <div className="card chart-card">
      <h2 className="card-title">Synthetic TVL Trend</h2>
      <div style={{ height: "240px" }}>
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}
