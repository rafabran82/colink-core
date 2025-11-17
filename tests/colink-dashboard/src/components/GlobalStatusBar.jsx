import React, { useEffect, useState } from "react";
import SystemAPI from "../api/system";

/**
 * GlobalStatusBar
 * Shows a persistent red/green status bar depending on backend health.
 */
export default function GlobalStatusBar() {
    const [ok, setOk] = useState(true);

    async function check() {
        const h = await SystemAPI.getHealth();
        setOk(!h.error);
    }

    useEffect(() => {
        check();
        const timer = setInterval(check, 5000);
        return () => clearInterval(timer);
    }, []);

    const style = {
        width: "100%",
        padding: "6px",
        textAlign: "center",
        fontSize: "14px",
        fontWeight: "600",
        background: ok ? "#003300" : "#330000",
        borderBottom: ok ? "1px solid #00ff00" : "1px solid #ff0000",
        color: ok ? "#00ff00" : "#ff0000",
        position: "fixed",
        top: 0,
        left: 0,
        zIndex: 9999,
    };

    return (
        <div style={style}>
            {ok ? "🟢 Backend Online" : "🔴 Backend Offline — retrying..."}
        </div>
    );
}
