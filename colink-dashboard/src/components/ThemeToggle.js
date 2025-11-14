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
      {theme === "dark" && "ðŸŒ™"}
      {theme === "neon" && "ðŸ'¡"}
      {theme === "future" && "ðŸš€"}
    </button>
  );
}