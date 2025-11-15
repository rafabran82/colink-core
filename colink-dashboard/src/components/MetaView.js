import React from "react";

export default function MetaView({ meta }) {
  if (!meta) {
    return <div>No metadata available.</div>;
  }

  return (
    <div>
      <h2>Simulation Meta</h2>
      <div><b>Run ID:</b> {meta.run_id || "unknown"}</div>
      <div><b>Timestamp:</b> {meta.timestamp || "unknown"}</div>
      <div><b>Params:</b></div>
      <pre style={{ background: "#111", padding: "1rem", borderRadius: "6px" }}>
        {JSON.stringify(meta.params || {}, null, 2)}
      </pre>
    </div>
  );
}

