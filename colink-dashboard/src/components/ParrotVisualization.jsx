import React from "react";

export default function ParrotVisualization() {
  const styles = getComputedStyle(document.body);

  const textColor = styles.getPropertyValue("--text-primary")?.trim() || "#fff";
  const secondary = styles.getPropertyValue("--text-secondary")?.trim() || "#999";
  const accent = styles.getPropertyValue("--accent")?.trim() || "#4cc2ff";

  const isDark = document.body.classList.contains("dark-mode");

  return (
    <div
      className="card"
      style={{
        padding: "24px",
        borderRadius: "16px",
        textAlign: "center",
        color: textColor,
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Optional neon ring in Dark Mode */}
      {isDark && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "inherit",
            boxShadow: `0 0 40px 4px ${accent}33`,
            pointerEvents: "none",
          }}
        />
      )}

      <h2 style={{ marginBottom: "15px", color: accent }}>
        🦜 Parrot Status
      </h2>

      <p style={{ fontSize: "16px", color: secondary }}>
        The parrot is monitoring TVL fluctuations and system activity.
      </p>

      <img
        src="./parrot-frames/colink_parrot_normal.gif"
        alt="Parrot Animation"
        style={{
          width: "180px",
          marginTop: "20px",
          filter: isDark ? "brightness(1.2)" : "brightness(1.0)",
        }}
      />
    </div>
  );
}
