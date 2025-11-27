import React, { useEffect, useRef, useState } from "react";
import Chart from "chart.js/auto";

export default function Charts() {
    const chartRef1 = useRef(null);
    const chart1 = useRef(null);
    const [xrpl, setXrpl] = useState(null);

    useEffect(() => {
    if (!xrpl) return;

    // Wait a moment for layout to stabilize
    setTimeout(() => {
        const canvas = chartRef1.current;
        if (!canvas) return;

        const width = canvas.clientWidth;
        const height = canvas.clientHeight;

        console.log("Chart container size:", width, height);

        // Retry once if size is still zero
        if (width <= 0 || height <= 0) {
            console.warn("Retrying chart render due to zero size...");
            setTimeout(() => setXrpl({ ...xrpl }), 20);
            return;
        }

        const ctx1 = canvas.getContext("2d");

        if (chart1.current) chart1.current.destroy();

        const labels = ["Seq", "Owners", "Balance"];
        const values = [
            xrpl.sequence || 0,
            xrpl.ownerCount || 0,
            xrpl.xrpBalance || 0,
        ];

        chart1.current = new Chart(ctx1, {
            type: "line",
            data: {
                labels,
                datasets: [{
                    label: "XRPL Live Metrics",
                    data: values,
                    borderColor: "#FFD400",
                    borderWidth: 3,
                    tension: 0.25,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
            },
        });
    }, 10);
}, [xrpl]);

    return (
        <div className="chart-stable-wrapper">
            <div className="chart-fixed-container" style={{ width: "100%", height: "360px", minHeight: "360px" }}>
    <canvas ref={chartRef1}></canvas>
</div>
        </div>
    );
}


