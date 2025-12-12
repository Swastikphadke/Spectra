import express from "express";
import fs from "fs";
import cors from "cors";
import path from "path";
import nodemailer from "nodemailer";
import dotenv from "dotenv";
dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

// ---------------------- DATA FILE SETUP ------------------------
const dataPath = path.join(process.cwd(), "data");
const usersFile = path.join(dataPath, "users.json");
const pendingOtpFile = path.join(dataPath, "pendingOtps.json");

if (!fs.existsSync(dataPath)) fs.mkdirSync(dataPath);
if (!fs.existsSync(usersFile)) fs.writeFileSync(usersFile, "[]");
if (!fs.existsSync(pendingOtpFile)) fs.writeFileSync(pendingOtpFile, "[]");

// Load OTPs
let pendingOtps = JSON.parse(fs.readFileSync(pendingOtpFile, "utf8"));

const savePendingOtps = () => {
  fs.writeFileSync(pendingOtpFile, JSON.stringify(pendingOtps, null, 2));
};

// ---------------------- SMTP CONFIG ---------------------------
let transporter;

if (process.env.SMTP_USER && process.env.SMTP_PASS) {
  transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST || "smtp.gmail.com",
    port: process.env.SMTP_PORT || 587,
    secure: false,
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    },
  });

  console.log("✔ SMTP mailer configured");
} else {
  console.log("❗ Running in DEV MODE: Emails will not be sent.");
}

// ---------------------- ROOT ROUTE -----------------------------
app.get("/", (req, res) => {
  res.send("AgroSat Backend is running ✔");
});

// ---------------------- SEND OTP -------------------------------
app.post("/send-otp", async (req, res) => {
  const { email, role } = req.body;

  if (!email) return res.json({ success: false, error: "Email required" });

  const otp = Math.floor(100000 + Math.random() * 900000).toString();

  pendingOtps.push({
    email,
    otp,
    role,
    timestamp: Date.now()
  });

  savePendingOtps();

  console.log("Generated OTP:", otp, "for", email);

  if (transporter) {
    try {
      await transporter.sendMail({
        from: process.env.EMAIL_FROM || process.env.SMTP_USER,
        to: email,
        subject: "Your AgroSat OTP Verification Code",
        text: `Your OTP is: ${otp}`,
        html: `<h2>Your OTP Code</h2><p style="font-size:18px;"><b>${otp}</b></p>`,
      });

      return res.json({ success: true });
    } catch (err) {
      console.log("Email error:", err);
      return res.json({ success: false, error: "Failed to send email" });
    }
  }

  return res.json({ success: true, devMode: true });
});

// ---------------------- VERIFY OTP -----------------------------
app.post("/verify-otp", (req, res) => {
  const { email, otp } = req.body;

  const entry = pendingOtps.find((o) => o.email === email && o.otp === otp);

  if (!entry) {
    return res.json({ success: false, error: "Invalid OTP" });
  }

  pendingOtps = pendingOtps.filter((o) => o !== entry);
  savePendingOtps();

  return res.json({ success: true });
});

// ---------------------- SAVE USER ------------------------------
app.post("/save", (req, res) => {
  const user = req.body;

  const existing = JSON.parse(fs.readFileSync(usersFile, "utf8"));
  existing.push(user);

  fs.writeFileSync(usersFile, JSON.stringify(existing, null, 2));

  res.json({ success: true });
});

// ---------------------- GET USERS ------------------------------
app.get("/users", (req, res) => {
  const users = JSON.parse(fs.readFileSync(usersFile, "utf8"));
  res.json(users);
});

// ---------------------- START SERVER ---------------------------
app.listen(8000, () => {
  console.log("✔ Backend API running at http://localhost:8000");
});
