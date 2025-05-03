require("dotenv").config(); // load .env at the very top
const { Client } = require("pg");
const fs = require("fs");
const path = require("path");
const simpleGit = require("simple-git");

const git = simpleGit();

const DB_CONFIG = {
  user: process.env.PG_USER,
  host: process.env.PG_HOST,
  database: process.env.PG_DATABASE,
  password: process.env.PG_PASSWORD,
  port: parseInt(process.env.PG_PORT, 10),
};

const FILE_PATH = path.join(__dirname, "data.json");
const GIT_COMMIT_MSG = "Update JSON data";

const QUERY = "SELECT * FROM ranked.seasons";

async function fetchDataAndUpdateFile() {
  const client = new Client(DB_CONFIG);

  try {
    await client.connect();
    const res = await client.query(QUERY);
    const data = res.rows;

    fs.writeFileSync(FILE_PATH, JSON.stringify(data, null, 2));
    console.log("✔ Data written to JSON file.");

    await git.add("data.json");
    await git.commit(GIT_COMMIT_MSG);
    await git.push();
    console.log("🚀 Pushed to GitHub.");
  } catch (err) {
    console.error("❌ Error:", err);
  } finally {
    await client.end();
  }
}

// Run once immediately
fetchDataAndUpdateFile();

// Run every hour
setInterval(fetchDataAndUpdateFile, 60 * 60 * 1000);
