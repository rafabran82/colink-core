// src/ParrotIntroPortal.js
import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom";
import "./ParrotIntro.css";

export default function ParrotIntroPortal({ onFinish }) {
    const [stage, setStage] = useState("enter"); 
    // stages: "enter"  "fade"  "done"

    useEffect(() => {
        // 1. animation lasts ~1.2s
        const animTimer = setTimeout(() => {
            setStage("fade");
        }, 1200);

        // 2. fade-out lasts 0.5s
        const fadeTimer = setTimeout(() => {
            setStage("done");
            onFinish && onFinish();
        }, 1200 + 500);

        return () => {
            clearTimeout(animTimer);
            clearTimeout(fadeTimer);
        };
    }, [onFinish]);

    if (stage === "done") return null;

    return ReactDOM.createPortal(
        <div className={`parrot-intro-overlay ${stage === "fade" ? "fade-out" : ""}`}>
            <div className="parrot-intro"></div>
        </div>,
        document.body
    );
}

