/*
  WebSocket live feed for COLINK dashboard.
  Backend must expose ws://localhost:8000/ws or wss://Ã¢â‚¬Â¦ in production.
*/

export function connectWS(onMessage) {
  const url = (window.location.hostname === "localhost")
    ? "ws://localhost:8000/ws"
    : `wss://${window.location.hostname}/ws`;

  let ws = new WebSocket(url);

  ws.onopen = () => console.log("[WS] Connected:", url);
  ws.onclose = () => {
    console.warn("[WS] Disconnected. Reconnecting in 2s...");
    setTimeout(() => connectWS(onMessage), 2000);
  };
  ws.onerror = (err) => console.error("[WS] Error:", err);
  ws.onmessage = (msg) => {
    try {
      const data = JSON.parse(msg.data);
      onMessage(data);
    } catch (e) {
      console.error("[WS] Bad message:", msg.data);
    }
  };

  return ws;
}
