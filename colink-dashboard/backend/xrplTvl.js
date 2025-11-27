const xrpl = require("xrpl");

// Synthetic TVL calculation
async function getXRPLTVL() {
    try {
        const client = new xrpl.Client("wss://s.altnet.rippletest.net:51233");
        await client.connect();

        const server = await client.request({ command: "server_info" });
        const ledger = server.result.info.validated_ledger;

        const seq = ledger.seq || ledger.sequence;
        const txs = ledger.txn_count || 0;
        const baseFee = ledger.base_fee_xrp || 0;

        // Synthetic stability metric
        const syntheticTVL =
            (seq % 1000000) * 0.5 +
            txs * 200 +
            baseFee * 100000;

        await client.disconnect();

        return {
            ledgerIndex: seq,
            txnCount: txs,
            baseFee,
            tvl: Number(syntheticTVL.toFixed(2)),
            timestamp: new Date().toISOString(),
        };

    } catch (err) {
        console.error("XRPL TVL error:", err);
        return { error: "Failed to load XRPL TVL", details: err.message };
    }
}


module.exports = { getXRPLTVL };

