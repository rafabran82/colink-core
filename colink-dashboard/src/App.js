import React from "react";
import PoolsView from "./components/PoolsView";
import SwapLogsView from "./components/SwapLogsView";
import MetaView from "./components/MetaView";

function App() {
  return (
    <div style={{ padding: "20px", fontFamily: "sans-serif" }}>
      <h1>COLINK Dashboard</h1>
      <MetaView />
      <PoolsView />
      <SwapLogsView />
    </div>
  );
}

export default App;
