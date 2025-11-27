import React from "react";

export default function DarkToggle({ toggleDark }) {
  return (
    <button
      onClick={toggleDark}
      style={{
        padding: "8px 14px",
        borderRadius: "8px",
        cursor: "pointer",
        backgroundColor: "#222",
        color: "white",
        border: "1px solid #444",
        position: "fixed",
        top: "20px",
        right: "20px",
        zIndex: 9999
      }}
    >
       Dark Mode
    </button>
  );
}

