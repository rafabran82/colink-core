const xrpl = require("xrpl");

// Use your generated testnet account
const ADDRESS = "rKPBpbtjoDeGNeSidGbapbrMw3NYnxs9kx";

async function fetchAccountInfo() {
  const client = new xrpl.Client("wss://s.altnet.rippletest.net:51233");

  console.log("Connecting to XRPL Testnet...");
  await client.connect();

  try {
    const response = await client.request({
      command: "account_info",
      account: ADDRESS,
      ledger_index: "validated"
    });

    console.log("Connected to XRP Testnet!");
    console.log("Account Info:", response.result.account_data);
    console.log("Account Balance:", response.result.account_data.Balance + " XRP");
  } catch (err) {
    console.error("Error fetching account info:", err);
  }

  await client.disconnect();
}

// Use proper async wrapper
(async () => {
  await fetchAccountInfo();
  process.exit(0);
})();
