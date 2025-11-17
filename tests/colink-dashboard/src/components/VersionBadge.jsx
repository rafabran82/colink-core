import React, { useEffect, useState } from "react";
import SystemAPI from "../api/system";

/**
 * Version Badge
 * Displays COLINK backend version + environment, with status indicator.
 */
export default function VersionBadge() {
    const [version, setVersion] = useState(null);
    const [ok, setOk] = useState(true);

    useEffect(() => {
        async function load() {
            const v = await SystemAPI.getVersion();
            if (v.error) {
                setOk(false);
            } else {
                setVersion(v);
                setOk(true);
            }
        }
        load();
    }, []);

    const style = {
        padding: "4px 10px",
        background: "#222",
        borderRadius: "8px",
        color: "#fff",
        display: "inline-flex",
        alignItems: "center",
        fontSize: "14px",
        gap: "6px",
        border: ok ? "1px solid #0f0" : "1px solid #f00"
    };

    return (
        <div style={style}>
            {ok ? <span style={{ color: "#0f0" }}>🟢</span> : <span style={{ color: "#f00" }}>🔴</span>}
            {version
                ? <>API v{version.version} — {version.env}</>
                : "Loading..."
            }
        </div>
    );
}
