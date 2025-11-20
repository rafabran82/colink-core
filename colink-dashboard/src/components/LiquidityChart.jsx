import React, { useEffect, useState } from 'react';
import '../App.css';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function LiquidityChart() {
    const [points, setPoints] = useState([]);

    useEffect(() => {
        async function load() {
            try {
                const res = await fetch('http://localhost:5000/api/xrpl/tvl');
                const data = await res.json();

                setPoints(prev => {
                    const next = [...prev, {
                        time: new Date(data.timestamp).toLocaleTimeString(),
                        tvl: data.tvl
                    }];

                    return next.slice(-20);  // keep last 20 points
                });
            } catch (err) {
                console.error('TVL fetch error:', err);
            }
        }

        load();
        const interval = setInterval(load, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="card" style={{ padding: '20px', minHeight: '260px' }}>
            <h3 style={{ marginBottom: '10px' }}> TVL Trend (Live)</h3>

            {points.length < 2 ? (
                <p>Loading chart...</p>
            ) : (
                <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={points}>
                        <XAxis dataKey="time" stroke="#888" />
                        <YAxis stroke="#888" />
                        <Tooltip />
                        <Line
                            type="monotone"
                            dataKey="tvl"
                            stroke="#00c2ff"
                            strokeWidth={3}
                            dot={false}
                        />
                    </LineChart>
                </ResponsiveContainer>
            )}
        </div>
    );
}

