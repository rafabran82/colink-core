import React, { useState, useEffect } from 'react';
import LiquidityChart from './components/LiquidityChart';
import ParrotVisualization from './components/ParrotVisualization';
import './App.css';
import './index.css';

function App() {
    const [dark, setDark] = useState(false);

    // Sync React state with <body> classes
    useEffect(() => {
        if (dark) {
            document.body.classList.add('dark-mode');
            document.body.classList.remove('light-mode');
        } else {
            document.body.classList.add('light-mode');
            document.body.classList.remove('dark-mode');
        }
    }, [dark]);

    const toggleDark = () => setDark(prev => !prev);

    return (
        <>
            <button className="dark-toggle-btn" onClick={toggleDark}>
                {dark ? ' Light Mode' : ' Dark Mode'}
            </button>

            <div className="dashboard-container">
                <LiquidityChart />
                <ParrotVisualization />
            </div>
        </>
    );
}

export default App;


