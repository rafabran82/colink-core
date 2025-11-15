const xrpl = require('xrpl');

// Connect to the XRP testnet
async function connect() {
  const client = new xrpl.Client('wss://s.altnet.rippletest.net:51233'); // XRP Testnet endpoint

  await client.connect();
  console.log('Connected to XRP Testnet!');

  // Get the current ledger
  const ledger = await client.request({
    command: 'ledger',
    ledger_index: 'validated'
  });

  console.log('Current Ledger:', ledger);

  await client.disconnect();
}

connect();
