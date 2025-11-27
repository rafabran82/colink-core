# XRPL Architecture & Flows — COLINK

## 1. Wallet Model

### Issuer Wallet  
- Issues COPX, COL  
- Must maintain high XRP reserve  

### User Wallet  
- Holds balances  
- Receives payments  

### LP Wallet  
- Provides liquidity to DEX pools  
- Controlled by project ops  

Stored in wallets.json with:  
- classic address  
- seed  
- private key  
- balance  
- trustlines  

---

## 2. Token Issuance (XLS-20 / IOU)

### IOU Token  
currency: 434F505800000000000000000000000000000000 (COPX)
issuer: <issuer_address>
value: <amount>

yaml
Copy code

### Trustlines  
Trustlines created for user and LP wallets.

---

## 3. DEX Liquidity Flow

### Liquidity Seeding Flow
1. Check existing trustlines  
2. Create issued currency offer  
3. Submit signed Tx  
4. Use safe_sign_and_autofill_transaction  
5. Confirm via ledger index  
6. Poll orderbook  

### AMM/DEX Offer
OfferCreate:
TakerPays: XRP
TakerGets: COPX

yaml
Copy code

Error sources:  
- tecUNFUNDED_OFFER  
- tecNO_LINE  
- tefBAD_AUTH  

---

## 4. Orderbook Fetch Logic

Correct XRPL spec requires:
taker_gets: { currency, issuer? }
taker_pays: { currency, issuer? }

yaml
Copy code

XRP must NOT have issuer.

---

## 5. Bootstrap Script Architecture

xrpl.testnet.bootstrap.py
- Creates/loads wallets  
- Funds from faucet  
- Sets trustlines  
- Validates via account_info  
- Provides JSON export  

---

## 6. Future XRPL Integrations

### COLINK Payment Rail  
- Multi-asset pathfinding  
- Slippage tolerance  
- Fee customization  
- Settlement traceability  

### COPX Bridge Prototype  
- Simulate COP ↔ COPX  
- Testnet routing  
- Settlement windows  

