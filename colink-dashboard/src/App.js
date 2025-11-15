import React, { useState, useEffect, useMemo } from "react";
import "./index.css";
import { fetchPools } from "./api/pools";
import { fetchAccountBalance } from "./api/account";

import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function getInitialTheme() {
  if (typeof window === "undefined") return "light";
  const stored = window.localStorage.getItem("theme");
  return stored === "dark" ? "dark" : "light";
}

function App() {
  const [accountBalance, setAccountBalance] = useState(null);
  const [theme, setTheme] = useState(getInitialTheme());
  const [pools, setPools] = useState([]);  // TEMP DEBUG: log pools when loaded
  useEffect(() => {
    console.log("POOLS RAW:", pools);
  }, [pools]);
  const [loadingPools, setLoadingPools] = useState(true);

  // Load pools from the backend
useEffect(() => {
  async function load() {
    try {
      const data = await fetchPools();
      console.log("Fetched pools:", data);
      setPools(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to fetch pools:", err);
      setPools([]);
    } finally {
      setLoadingPools(false);
    }
  }
  load();
}, []);

  // Apply / persist theme
  useEffect(() => {
    if (theme === "dark") {
      document.body.classList.add("dark-mode");
    } else {
      document.body.classList.remove("dark-mode");
    }

    if (typeof window !== "undefined") {
      window.localStorage.setItem("theme", theme);
    }
  }, [theme]);

  const toggleDarkMode = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  // Demo data to use when backend returns no pools
  const demoPools = [
    { pair: "COPX/COL", reserve1: 0.8, reserve2: 0.2 },
    { pair: "COL/XRP", reserve1: 0.6, reserve2: 0.4 },
  ];

  // Build chart data from pools (or demo pools)
  const chartData = useMemo(() => {
    const sourcePools =
      pools && pools.length > 0 ? pools : demoPools;

    const labels = sourcePools.map((p) =>
      p.pair || (p.asset1 && p.asset2 ? `${p.asset1}/${p.asset2}` : "Pool")
    );

    const reserve1 = sourcePools.map((p) =>
      Number(
        p.reserve1 != null
          ? p.reserve1
          : p.reserve_1 != null
          ? p.reserve_1
          : 0
      )
    );
    const reserve2 = sourcePools.map((p) =>
      Number(
        p.reserve2 != null
          ? p.reserve2
          : p.reserve_2 != null
          ? p.reserve_2
          : 0
      )
    );

    const color1 =
      theme === "dark"
        ? "rgba(56, 189, 248, 0.7)" // cyan-ish
        : "rgba(59, 130, 246, 0.7)"; // blue

    const color2 =
      theme === "dark"
        ? "rgba(248, 113, 113, 0.7)" // red
        : "rgba(244, 63, 94, 0.7)"; // pink/red

    return {
      labels,
      datasets: [
        {
          label: "Reserve 1",
          data: reserve1,
          backgroundColor: color1,
        },
        {
          label: "Reserve 2",
          data: reserve2,
          backgroundColor: color2,
        },
      ],
    };
  }, [pools, theme, demoPools]);

  // Chart options (auto-scale based on data, theme-aware axes)
  const chartOptions = useMemo(() => {
    const allValues = chartData.datasets.reduce((acc, ds) => {
      const data = Array.isArray(ds.data) ? ds.data : [];
      return acc.concat(data);
    }, []);

    const maxValue = allValues.length ? Math.max.apply(null, allValues) : 1;

    const axisColor = theme === "dark" ? "#9ca3af" : "#4b5563";
    const gridColor =
      theme === "dark"
        ? "rgba(55, 65, 81, 0.7)"
        : "rgba(209, 213, 219, 0.7)";
    const legendColor = theme === "dark" ? "#e5e7eb" : "#111827";

    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
          labels: {
            color: legendColor,
          },
        },
        title: {
          display: false,
        },
      },
      scales: {
        x: {
          ticks: {
            color: axisColor,
          },
          grid: {
            color: gridColor,
          },
        },
        y: {
          beginAtZero: true,
          suggestedMax: maxValue * 1.1,
          ticks: {
            color: axisColor,
          },
          grid: {
            color: gridColor,
          },
        },
      },
    };
  }, [chartData, theme]);

  useEffect(() => {
    const loadBalance = async () => {
      try {
        const balance = await fetchAccountBalance();
        setAccountBalance(balance);
      } catch (err) {
        console.error("Failed to fetch account balance", err);
      }
    };
    loadBalance();
  }, []);

  return (
    <div className={`app ${theme}`}>
      <button
        onClick={toggleDarkMode}
        style={{
          position: "absolute",
          top: 10,
          right: 10,
          padding: "6px 12px",
          borderRadius: "999px",
          border: "none",
          cursor: "pointer",
        }}
      >
        {theme === "dark" ? "Light mode" : "Dark mode"}
      </button>

      <div className="dashboard">
        <h1>COLINK Dashboard</h1>

        <section style={{ height: "340px", maxWidth: "900px" }}>
          <h2>Pools</h2>

          {loadingPools ? (
            <p>Loading poolsâ€¦</p>
          ) : (
            <>
              <Bar data={chartData} options={chartOptions} />
              {pools.length === 0 ? (
                <p
                  style={{
                    marginTop: 8,
                    fontSize: "0.85rem",
                    opacity: 0.8,
                  }}
                >
                  Showing demo data (no pools returned from API).
                </p>
              ) : (
                <p
                  style={{
                    marginTop: 8,
                    fontSize: "0.85rem",
                    opacity: 0.8,
                  }}
                >
                  Showing {pools.length} pool
                  {pools.length > 1 ? "s" : ""} from backend.
                </p>
              )}
            </>
          )}
                <div style={{
          marginTop: '20px',
          padding: '16px',
          borderRadius: '12px',
          background: theme === 'dark' ? '#1f2937' : '#f3f4f6',
          boxShadow: '0px 2px 6px rgba(0,0,0,0.15)',
          maxWidth: '300px'
        }}>
          <h3 style={{ marginBottom: '8px' }}>Account Balance</h3>
          <p style={{ fontSize: '22px', fontWeight: 'bold' }}>
            {accountBalance !== null ? accountBalance + ' XRP' : 'Loading…'}
          </p>
        </div>
</section>
      </div>
    </div>
  );
}

export default App;


















