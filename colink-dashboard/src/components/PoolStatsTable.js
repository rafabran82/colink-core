import React from "react";

function PoolStatsTable({ pools }) {
  if (!pools || pools.length === 0) {
    return (
      <p style={{ color: "var(--text)", padding: "12px" }}>
        No pool data available.
      </p>
    );
  }

  return (
    <table
      style={{
        width: "100%",
        borderCollapse: "collapse",
        marginTop: "24px",
        fontSize: "0.9rem",
        background: "var(--card-bg)",
      }}
    >
      <thead>
        <tr style={{ background: "var(--card-bg)", color: "var(--text-faded)" }}>
          <th style={th}>Pool</th>
          <th style={th}>Base Liquidity</th>
          <th style={th}>Quote Liquidity</th>
          <th style={th}>LP Supply</th>
          <th style={th}>Fee (bps)</th>
          <th style={th}>Updated</th>
        </tr>
      </thead>

      <tbody>
        {pools.map((p, i) => (
          <tr key={i} style={row}>
            <td style={td}>{p.label}</td>
            <td style={tdRight}>{p.baseLiquidity.toLocaleString()}</td>
            <td style={tdRight}>{p.quoteLiquidity.toLocaleString()}</td>
            <td style={tdRight}>{p.lpTokenSupply.toLocaleString()}</td>
            <td style={tdRight}>{p.feeBps}</td>
            <td style={td}>{new Date(p.lastUpdated).toLocaleTimeString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

const th = {
  padding: "8px",
  textAlign: "left",
  borderBottom: "1px solid var(--border)",
};

const td = {
  padding: "8px",
  color: "var(--text)",
  borderBottom: "1px solid var(--border)",
};

const tdRight = {
  ...td,
  textAlign: "right",
};

const row = {
  background: "var(--card-bg)",
};

export default PoolStatsTable;
