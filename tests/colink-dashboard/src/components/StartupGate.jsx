import React, { useEffect, useState } from "react";
import SystemAPI from "../api/system";
import GlobalStatusBar from "./GlobalStatusBar";

/**
 * StartupGate
 * Blocks dashboard rendering until backend is confirmed reachable.
 */
export default function StartupGate({ children }) {
    const [ready, setReady] = useState(false);
    const [offline, setOffline] = useState(false);

    async function check() {
        const h = await SystemAPI.getHealth();
        if (h.error) {
            setOffline(true);
            setReady(false);
        } else {
            setOffline(false);
            setReady(true);
        }
    }

    useEffect(() => {
        check();
        const timer = setInterval(check, 5000);
        return () => clearInterval(timer);
    }, []);

    if (!ready) {
        return (
            <div style={{
                background: "#000",
                color: "#fff",
                height: "100vh",
                width: "100vw",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexDirection: "column",
                gap: "12px",
                fontSize: "20px"
            }}>
                <GlobalStatusBar />
                <div>🔴 Backend Offline</div>
                <div style={{ fontSize: "14px", opacity: 0.7 }}>Retrying...</div>
            </div>
        );
    }

    // Backend is online → render the actual app
    return (
        <>
            <GlobalStatusBar />
            {children}
        </>
    );
}
