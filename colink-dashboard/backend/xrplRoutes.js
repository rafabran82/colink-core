const express = require("express");
const router = express.Router();
const { Client, Wallet } = require("xrpl");

const RPC = "wss://s.altnet.rippletest.net:51233";  // XRPL Testnet WebSocket

const USER_SEED = "sEd79uZimDdjTin635hgAWhQWYCfSdm"; 
const wallet = Wallet.fromSeed(USER_SEED);

const ISSUER = "ravH5waBisEj3NJNd3bQjQUreJJ56FFQRM";

// =====================================================
// GET ACCOUNT INFO
// =====================================================
router.get("/account", async (req, res) => {
    const client = new Client(RPC);
    await client.connect();

    const info = await client.request({
        command: "account_info",
        account: wallet.address,
        ledger_index: "validated"
    });

    const lines = await client.request({
        command: "account_lines",
        account: wallet.address
    });

    client.disconnect();

    res.json({
        address: wallet.address,
        xrpBalance: info.result.account_data.Balance / 1_000_000,
        sequence: info.result.account_data.Sequence,
        ownerCount: info.result.account_data.OwnerCount,
        tokens: lines.result.lines
    });
});

// =====================================================
// CREATE TRUSTLINE
// =====================================================
router.post("/trustline", async (req, res) => {
    const { code } = req.body;
    if (!code) return res.json({ error: "Missing code" });

    const client = new Client(RPC);
    await client.connect();

    try {
        const tx = {
            TransactionType: "TrustSet",
            Account: wallet.address,
            LimitAmount: {
                currency: code,
                issuer: ISSUER,
                value: "10000000"
            }
        };

        const prepared = await client.autofill(tx);
        const signed = wallet.sign(prepared);
        const result = await client.submitAndWait(signed.tx_blob);

        client.disconnect();

        return res.json({
            status: result.result.meta.TransactionResult
        });
    } catch (err) {
        return res.json({ error: err.message });
    }
});

router.get('/tvl', async (req, res) => {
    const { getXRPLTVL } = require('./xrplTvl');
    const tvl = await getXRPLTVL();
    res.json(tvl);
});
module.exports = router;



