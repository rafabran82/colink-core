const express = require("express");
const app = express();
const port = 3000;

// Sample route to check server status
app.get("/", (req, res) => {
  res.send("COLINK Backend is running!");
});

app.listen(port, () => {
  console.log(`Server is running at http://localhost:${port}`);
});
