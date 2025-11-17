import React, { useEffect, useState } from "react";
import SystemAPI from "../api/system";

/**
 * System Status Panel
 * Displays backend health, version, config, and status.
 */
export default function SystemStatusPanel() {
    const [health, setHealth] = useState(null);
    const [version, setVersion] = useState(null);
    const [config, setConfig] = useState(null);
    const [status, setStatus] = useState(null);

    useEffect(() => {
        async function fetchData() {
            const h = await SystemAPI.getHealth();
            const v = await SystemAPI.getVersion();
            const c = await SystemAPI.getConfig();
            const s = await SystemAPI.getStatus();

            setHealth(h);
            setVersion(v);
            setConfig(c);
            setStatus(s);
        }
        fetchData();
    }, []);

    const ok = health && !health.error;

    return (
        <div style={{
            padding: "16px",
            margin: "16px 0",
            background: "#111",
            borderRadius: "12px",
            border: ok ? "1px solid #0f0" : "1px solid #f00",
            color: "#fff",
        }}>
            <h2 style={{ marginTop: 0 }}>System Status</h2>

            <p>
                Status:{" "}
                {ok ? <span style={{ color: "#0f0" }}>🟢 Online</span> : <span style={{ color: "#f00" }}>🔴 Offline</span>}
            </p>

            {version && (
                <p>Version: <strong>{version.version}</strong> ({version.env})</p>
            )}

            {config && (
                <>
                    <p>XRPL Network: <strong>{config.xrpl_network}</strong></p>
                    <p>Simulation Mode: <strong>{config.sim_mode}</strong></p>
                </>
            )}

            {status && (
                <p>Backend Status: <strong>{status.status}</strong></p>
            )}
        </div>
    );
}
