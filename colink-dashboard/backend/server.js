const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');

const app = express();
const port = 5000;

app.use(cors());
app.use(express.json());

// Simple root route to verify server is alive
app.get('/', (req, res) => {
  res.send('Backend is alive');
});

// Route to log pool data
app.post('/log-pools', (req, res) => {
  console.log('Pools data received:', req.body);
  res.status(200).send('Pools data logged');
});

// Route to fetch XRPL account info by calling xrplAccount.js
app.get('/get-account-info', async (req, res) => {
  try {
    console.log('[/get-account-info] calling xrplAccount.js ...');
    exec('node C:/Users/sk8br/Desktop/colink-core/colink-dashboard/backend/xrplAccount.js', (error, stdout, stderr) => {
      if (error) {
        console.error('exec error:', error);
        return res.status(500).send('Error fetching account data');
      }
      if (stderr) {
        console.error('stderr from xrplAccount.js:', stderr);
        // we still continue; stdout may contain the info we need
      }
      console.log('[/get-account-info] response:\n', stdout);
      res
        .status(200)
        .type('text/plain')
        .send(stdout);
    });
  } catch (error) {
    console.error('Error in /get-account-info handler:', error);
    res.status(500).send('Error fetching account info');
  }
});

app.get('/get-account-balance', async (req, res) => {
  try {
    const { exec } = require('child_process');
    exec('node xrplAccount.js', (error, stdout, stderr) => {
      if (error) {
        console.error("exec error:", error);
        return res.status(500).send("Error fetching account balance");
      }

      const match = stdout.match(/Balance:\s+'(\d+)'/);
      const drops = match ? match[1] : null;

      if (!drops) {
        return res.status(500).send("Could not parse balance");
      }

      const xrp = Number(drops) / 1_000_000;
      res.status(200).send(xrp.toString());
    });
  } catch (err) {
    console.error("handler error:", err);
    res.status(500).send("Error");
  }
});
app.listen(port, () => {
  console.log(`Backend server is running on port ${port}`);
});


