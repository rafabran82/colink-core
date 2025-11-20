import React from "react";
import "./ParrotIntro.css";
import finalLogo from "./colink_logo_final_solid.png";

export default function ParrotIntro() {
  return (
    <div className="intro-container">
      <div className="parrot-intro"></div>

      <img
        src={finalLogo}
        alt="COLINK Logo"
        className="final-logo"
      />
    </div>
  );
}
