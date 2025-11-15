import React from "react";

function SimMetaBar({ meta }) {
  if (!meta) return null;

  return (
    <div
      style={{
        background: "#f5f5f5",
        padding: "8px 16px",
        borderRadius: "6px",
        marginBottom: "18px",
        fontSize: "0.9rem",
        maxWidth: "fit-content",
        border: "1px solid #ddd",
      }}
    >
      <strong>Phase {meta.phase}</strong>
      {" Â· "}
      <span>{meta.network}</span>
      {" Â· "}
      <span>Run: {meta.runId}</span>
    </div>
  );
}

export default SimMetaBar;

