import React, { useState, useEffect } from "react";
import "./index.css";

import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from "chart.js";

import StartupGate from "./components/StartupGate";
import GlobalStatusBar from "./components/GlobalStatusBar";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

// Demo pool data (replace later with real API data)
const poolLabels = ["COPX/COL", "COL/XRP"];

const poolData = {
  labels: poolLabels,
  datasets: [
    {
      label: "Reserve 1",
      data: [0.8, 0.6],
      backgroundColor: "rgba(75, 192, 192, 0.5)",
    },
    {
      label: "Reserve 2",
      data: [0.2, 0.4],
      backgroundColor: "rgba(255, 99, 132, 0.5)",
    },
  ],
};

const poolOptions = {
  responsive: true,
  plugins: {
    legend: { position: "top" },
  },
};

function AppContent() {
  const [theme, setTheme] = useState(
    (typeof window !== "undefined" && window.localStorage.getItem("theme")) ||
      "light"
  );

  useEffect(() => {
    document.body.classList.toggle("dark-mode", theme === "dark");

    if (typeof window !== "undefined") {
      window.localStorage.setItem("theme", theme);
    }
  }, [theme]);

  const toggleDarkMode = () => {
    setTheme(prev => (prev === "dark" ? "light" : "dark"));
  };

  return (
    <div className="app">
      <GlobalStatusBar />

      <button
        onClick={toggleDarkMode}
        style={{ position: "absolute", top: 10, right: 10 }}
      >
        {theme === "dark" ? "Light mode" : "Dark mode"}
      </button>

      <div className="dashboard">
        <h1>COLINK Dashboard</h1>

        <section>
          <h2>Pools</h2>
          <Bar data={poolData} options={poolOptions} />
        </section>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <StartupGate>
      <AppContent />
    </StartupGate>
  );
}
