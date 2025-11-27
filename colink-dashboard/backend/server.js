const dns = require("dns");
dns.setDefaultResultOrder("ipv4first");
/**
 * COLINK Backend Server
 * Fully patched by automation
 */

const express = require("express");
const cors = require("cors");

// XRPL routes
const xrplRoutes = require("./xrplRoutes");

// TVL module
const { getXRPLTVL } = require("./xrplTvl.js");

const app = express();
app.use(cors());
app.use(express.json());

// --- XRPL ROUTES ---
app.use("/api/xrpl", xrplRoutes);

// --- DIRECT TVL ENDPOINT ---
app.get("/api/xrpl/tvl", async (req, res) => {
    try {
        const tvl = await getXRPLTVL();
        res.json(tvl);
    } catch (err) {
        console.error("TVL endpoint error:", err);
        res.status(500).json({ error: "Failed to fetch TVL" });
    }
});

// --- START SERVER ---
const PORT = 5000;

app.listen(PORT, () => {
    console.log(`🔥 COLINK Backend is running on port ${PORT}`);
});


