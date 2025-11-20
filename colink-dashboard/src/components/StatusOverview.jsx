import React, { useEffect, useState } from "react";
import "./StatusOverview.css";

export default function StatusOverview() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const res = await fetch("http://localhost:5000/get-account-info");
        const data = await res.json();
        setStatus(data);
      } catch (err) {
        console.error("Failed to load status overview:", err);
      }
    }
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!status) {
    return (
      <div className="status-card">
        <h2>COLINK STATUS OVERVIEW</h2>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="status-card">
      <h2>COLINK STATUS OVERVIEW</h2>

      <div className="status-grid">
        <div className="item">
          <span className="label">Ledger</span>
          <span className="value">{status.ledger_index}</span>
        </div>

        <div className="item">
          <span className="label">TX Count</span>
          <span className="value">{status.tx_count}</span>
        </div>

        <div className="item">
          <span className="label">Base Fee</span>
          <span className="value">{status.base_fee}</span>
        </div>
      </div>
    </div>
  );
}
