import React, { useContext } from "react";
import { ThemeContext } from "../context/ThemeContext";

export default function ThemeToggle() {
  const { theme, toggleTheme } = useContext(ThemeContext);

  return (
    <button
      onClick={toggleTheme}
      className="theme-toggle-btn"
      title="Change theme"
    >
      {theme === "dark" && "Ã°Å¸Å’â„¢"}
      {theme === "neon" && "Ã°Å¸'Â¡"}
      {theme === "future" && "Ã°Å¸Å¡â‚¬"}
    </button>
  );
}
