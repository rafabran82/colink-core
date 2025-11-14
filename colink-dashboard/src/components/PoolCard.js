import React, { useEffect, useState } from "react";

export default function PoolCard({ pool }) {
  const {
    label,
    baseSymbol,
    quoteSymbol,
    baseLiquidity,
    quoteLiquidity,
    lpTokenSupply,
    feeBps,
    lastUpdated,
  } = pool;

  // Flash animation on updates
  const [flash, setFlash] = useState(false);
  useEffect(() => {
    setFlash(true);
    const t = setTimeout(() => setFlash(false), 1200);
    return () => clearTimeout(t);
  }, [pool]);

  return (
    <div
      className={flash ? "flash-update" : ""}
      style={{
        marginTop: "12px",
        padding: "16px",
        borderRadius: "12px",
        border: "1px solid #555",
        backgroundColor: "rgba(255,255,255,0.03)",
      }}
    >
      <h3>{label}</h3>
      <p><strong>Base:</strong> {baseSymbol} - Liquidity: {baseLiquidity.toLocaleString()}</p>
      <p><strong>Quote:</strong> {quoteSymbol} - Liquidity: {quoteLiquidity.toLocaleString()}</p>
      <p><strong>LP Supply:</strong> {lpTokenSupply.toLocaleString()}</p>
      <p><strong>Fee:</strong> {feeBps} bps</p>
      <p style={{ fontSize: "0.8rem", opacity: 0.7 }}>
        Updated: {new Date(lastUpdated).toLocaleString()}
      </p>
    </div>
  );
}
