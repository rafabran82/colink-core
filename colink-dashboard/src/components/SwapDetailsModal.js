import React from "react";

export default function SwapDetailsModal({ swap, onClose }) {
  if (!swap) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>Swap Details</h2>

        <pre
          style={{
            background: "#000",
            padding: "1rem",
            borderRadius: "8px",
            overflowX: "auto",
            color: "white"
          }}
        >
{JSON.stringify(swap, null, 2)}
        </pre>

        <button className="modal-close-btn" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}