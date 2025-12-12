import express from "express";
import fs from "fs";
import cors from "cors";
import path from "path";

const app = express();
app.use(cors());
app.use(express.json());

const dataPath = path.join(process.cwd(), "data");
const filePath = path.join(dataPath, "users.json");

// ensure /data exists
if (!fs.existsSync(dataPath)) fs.mkdirSync(dataPath);

// ensure file exists
if (!fs.existsSync(filePath)) fs.writeFileSync(filePath, "[]");

app.post("/save", (req, res) => {
    const user = req.body;

    let existing = JSON.parse(fs.readFileSync(filePath, "utf8"));
    existing.push(user);

    fs.writeFileSync(filePath, JSON.stringify(existing, null, 2));
    res.json({ success: true });
});

app.get("/users", (req, res) => {
    const users = JSON.parse(fs.readFileSync(filePath, "utf8"));
    res.json(users);
});

app.listen(5000, () => {
    console.log("Backend API running on http://localhost:8000");
});
