import React from "react";
import { NavLink } from "react-router-dom";

function Navbar({ isDark }) {
  const linkStyle = {
    padding: "8px 16px",
    borderRadius: "6px",
    fontWeight: 500,
    textDecoration: "none",
    color: isDark ? "#f5f5f5" : "#222",
  };

  const activeStyle = {
    backgroundColor: isDark ? "#333" : "#ddd",
    color: isDark ? "#fff" : "#000",
  };

  return (
    <nav
      style={{
        padding: "12px 20px",
        borderBottom: isDark ? "1px solid #444" : "1px solid #ccc",
        marginBottom: "16px",
        display: "flex",
        gap: "12px",
      }}
    >
      <NavLink
        to="/"
        end
        style={({ isActive }) =>
          isActive ? { ...linkStyle, ...activeStyle } : linkStyle
        }
      >
        Dashboard
      </NavLink>

      <NavLink
        to="/swap-logs"
        style={({ isActive }) =>
          isActive ? { ...linkStyle, ...activeStyle } : linkStyle
        }
      >
        Swap Logs
      </NavLink>
    </nav>
  );
}

export default Navbar;
