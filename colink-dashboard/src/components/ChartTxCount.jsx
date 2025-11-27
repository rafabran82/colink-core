import React, { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import "chart.js/auto";

export default function ChartTxCount() {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch("http://localhost:5000/api/xrpl/tvl");
        const data = await res.json();

        const point = {
          time: new Date().toLocaleTimeString(),
          value: data.txnCount || 0,
        };

        setHistory((prev) => [...prev.slice(-20), point]);
      } catch (err) {
        console.error("TX Chart error:", err);
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
        label: "Transaction Count",
        data: history.map((p) => p.value),
        borderColor: "#ffdd55",
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
      <h2 className="card-title">XRPL Transaction Count</h2>
      <div style={{ height: "240px" }}>
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}
