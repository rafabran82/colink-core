# COLINK Dashboard — Full System Architecture

## 1. Components

### Frontend
- React  
- Recharts (for graphs)  
- Flash graph system  
- Dark mode system  
- API wrappers (src/api/*.js)  

### Backend
Node.js / Express  
Endpoints:
- /get-account-info
- /get-orderbook
- /get-pools
- /get-logs

---

## 2. Backend → XRPL

Backend calls Python or direct JS XRPL SDK.

### Example Flow:  
Frontend → /get-orderbook → backend → Python file → XRPL → JSON return.

---

## 3. Local CI Integration

Your local PowerShell CI generates:
- .artifacts/index.html
- charts  
- summaries  
- NDJSON logs  

Dashboard reads these as needed.

---

## 4. Data Model

### Account Info  
- address  
- XRP balance  
- trustlines  

### Pool Metrics  
- volatility  
- shocks  
- APY  
- LP share  

---

## 5. Performance Goals

- <200ms backend latency  
- <2s XRPL account calls  
- 60fps charting  
- JSON-first response architecture  

