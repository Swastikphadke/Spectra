import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { StarsBackground } from "@/components/StarsBackground";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Shield, ArrowLeft, Lock } from "lucide-react";
import { toast } from "@/hooks/use-toast";

// Backend running on port 8000
const API_BASE = "http://localhost:8000";

const InsuranceAuth = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    companyName: "",
    password: "",
    email: "",
  });

  const [otpSent, setOtpSent] = useState(false);
  const [otpValue, setOtpValue] = useState("");
  const [verified, setVerified] = useState(false);

  // -------------------- SEND OTP --------------------
  const sendOtp = async () => {
    if (!formData.email || !/^\S+@\S+\.\S+$/.test(formData.email)) {
      return toast({
        title: "Unable to Transmit",
        description: "Invalid comms channel (email).",
        variant: "destructive",
      });
    }

    try {
      const res = await fetch(`${API_BASE}/send-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: formData.email,
          role: "insurance",
        }),
      });

      const data = await res.json();
      if (data.success) {
        setOtpSent(true);
        toast({ 
          title: "Signal Transmitted", 
          description: "Authentication code sent through the breach.",
          className: "bg-cyan-950 border-cyan-500 text-cyan-100"
        });
      } else {
        toast({ title: "Transmission Error", description: data.error || "Failed to send OTP", variant: "destructive" });
      }
    } catch (error) {
       toast({ title: "Connection Failure", description: "Backend unreachable.", variant: "destructive" });
    }
  };

  // -------------------- VERIFY OTP --------------------
  const verifyOtp = async () => {
    if (!otpValue) {
      return toast({
        title: "Input Required",
        description: "Enter authorization sequence.",
        variant: "destructive",
      });
    }

    try {
      const res = await fetch(`${API_BASE}/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: formData.email,
          otp: otpValue,
        }),
      });

      const data = await res.json();
      if (data.success) {
        setVerified(true);
        toast({ 
            title: "Sequence Verified", 
            description: "Identity confirmed. Clearance granted.", 
            className: "bg-cyan-950 border-cyan-500 text-white" 
        });
      } else {
        toast({ title: "Access Denied", description: data.error || "Invalid OTP", variant: "destructive" });
      }
    } catch (error) {
        toast({ title: "Verification Error", variant: "destructive" });
    }
  };

  // -------------------- FINAL SUBMIT --------------------
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.companyName || !formData.password || !formData.email) {
      return toast({
        title: "Parameters Incomplete",
        description: "All fields required for launch sequence.",
        variant: "destructive",
      });
    }

    if (!verified) {
      return toast({
        title: "Verification Pending",
        description: "Verify comms channel before proceeding.",
        variant: "destructive",
      });
    }

    try {
        // Save to backend
        await fetch(`${API_BASE}/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            role: "insurance",
            companyName: formData.companyName,
            password: formData.password,
            email: formData.email,
            emailVerified: true,
            timestamp: new Date().toISOString(),
        }),
        });

        sessionStorage.setItem("insuranceCompany", formData.companyName);

        toast({
        title: "Docking Successful",
        description: `Welcome aboard the Endurance, ${formData.companyName}.`,
        className: "bg-white text-black border-white/50"
        });

        navigate("/insurance/dashboard");
    } catch (error) {
         toast({ title: "Docking Failed", description: "Could not save session data.", variant: "destructive" });
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] relative overflow-hidden font-sans selection:bg-cyan-500/30">
      <StarsBackground />
      
      {/* --- Background Atmospheric Effects --- */}
      
      {/* 1. Existing Cyan/Blue Nebula (Top Left) */}
      <div className="absolute top-[-20%] left-[-20%] w-[80%] h-[80%] rounded-full bg-gradient-to-br from-cyan-500/10 via-blue-900/5 to-transparent blur-[120px] pointer-events-none" />
      
      {/* 2. Existing Subtle Lower Glow (Bottom Right) */}
      <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full bg-gradient-to-tl from-white/5 via-blue-900/5 to-transparent blur-[100px] pointer-events-none opacity-50" />
      
      {/* 3. 🌑 NEW: The "Moon" / White Circle Fading Out (Top Right) */}
      <div 
        className="absolute top-[5%] right-[10%] w-[500px] h-[500px] rounded-full bg-white/30 blur-[150px] pointer-events-none opacity-60 mix-blend-soft-light"
        aria-hidden="true"
      />
      
      {/* ------------------------------------ */}

      <Navbar />

      <main className="relative z-10 pt-24 pb-16 container mx-auto px-4 flex flex-col items-center justify-center min-h-[85vh]">
        <div className="w-full max-w-md">
            <Button 
                variant="ghost" 
                onClick={() => navigate("/")} 
                className="mb-8 text-slate-400 hover:text-white hover:bg-white/5 transition-all uppercase tracking-widest text-xs font-bold pl-0"
            >
            <ArrowLeft className="w-4 h-4 mr-2" />
            {t("back")}
            </Button>

            <Card className="bg-black/40 border-white/10 backdrop-blur-xl shadow-[0_0_50px_-15px_rgba(6,182,212,0.15)]">
            <CardHeader className="text-center pb-2">
                <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-cyan-950 to-black border border-cyan-500/30 flex items-center justify-center mx-auto mb-4 shadow-[0_0_20px_rgba(6,182,212,0.2)] relative overflow-hidden">
                    <div className="absolute inset-0 bg-cyan-500/10 animate-pulse-slow rounded-full"></div>
                    <Shield className="w-10 h-10 text-cyan-100 relative z-10" />
                </div>
                <CardTitle className="text-3xl font-light text-white uppercase tracking-[0.15em]">
                    Spectra <span className="font-bold text-cyan-400">Secure</span>
                </CardTitle>
                <CardDescription className="text-slate-400 font-mono text-xs uppercase tracking-widest mt-2">
                    Insurance Provider Authorization Protocol
                </CardDescription>
            </CardHeader>

            <CardContent className="pt-6">
                <form onSubmit={handleSubmit} className="space-y-6">

                {/* Company Name */}
                <div className="space-y-2 group">
                    <Label htmlFor="companyName" className="text-slate-500 text-[10px] uppercase tracking-[0.2em] group-focus-within:text-cyan-400 transition-colors">
                        Organization ID
                    </Label>
                    <Input
                    id="companyName"
                    value={formData.companyName}
                    onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
                    placeholder="ENTER ENTITY NAME"
                    className="bg-white/5 border-white/10 text-white placeholder:text-white/20 font-mono text-sm h-12 focus:border-cyan-500/50 focus:ring-cyan-500/10 transition-all"
                    />
                </div>

                {/* Email */}
                <div className="space-y-2 group">
                    <Label className="text-slate-500 text-[10px] uppercase tracking-[0.2em] group-focus-within:text-cyan-400 transition-colors">
                        Comms Channel (Email)
                    </Label>
                    <Input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="SECURE@DOMAIN.COM"
                    className="bg-white/5 border-white/10 text-white placeholder:text-white/20 font-mono text-sm h-12 focus:border-cyan-500/50 focus:ring-cyan-500/10 transition-all"
                    />
                </div>

                {/* OTP Row */}
                <div className="space-y-2">
                     <Label className="text-slate-500 text-[10px] uppercase tracking-[0.2em]">
                        Security Clearance sequence
                    </Label>
                    <div className="flex gap-3">
                        <Button 
                        type="button" 
                        variant="outline" 
                        className="flex-1 bg-transparent border-white/20 text-cyan-200 hover:bg-cyan-950/30 hover:border-cyan-500/50 hover:text-white transition-all uppercase tracking-wider text-xs font-bold h-12" 
                        onClick={sendOtp}
                        disabled={verified || otpSent}
                        >
                        {otpSent ? "Signal Active" : "Send Code"}
                        </Button>
                        <Input
                        placeholder="XXX-XXX"
                        value={otpValue}
                        onChange={(e) => setOtpValue(e.target.value.replace(/\D/g, "").slice(0, 6))}
                        className="w-36 bg-black/50 border-white/20 text-center text-white font-mono tracking-[0.3em] text-lg focus:border-cyan-400/70 h-12 placeholder:text-white/10"
                        disabled={verified}
                        />
                        <Button 
                        type="button" 
                        variant="outline" 
                        onClick={verifyOtp}
                        disabled={verified}
                        className={`h-12 border-white/20 uppercase tracking-wider text-xs font-bold transition-all
                            ${verified 
                            ? "bg-cyan-950/50 border-cyan-500 text-cyan-300 hover:bg-cyan-950/50 opacity-100" 
                            : "hover:bg-white/10 hover:border-white/40 text-slate-300"
                            }`}
                        >
                        {verified ? "Clearance OK" : "Verify"}
                        </Button>
                    </div>
                </div>

                {/* Password */}
                <div className="space-y-2 group">
                    <Label htmlFor="password" className="text-slate-500 text-[10px] uppercase tracking-[0.2em] group-focus-within:text-cyan-400 transition-colors">
                        Access Key
                    </Label>
                    <div className="relative">
                        <Input
                        id="password"
                        type="password"
                        value={formData.password}
                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        placeholder="••••••••"
                        className="bg-white/5 border-white/10 text-white placeholder:text-white/20 font-mono text-sm h-12 pr-10 focus:border-cyan-500/50 focus:ring-cyan-500/10 transition-all"
                        />
                        <Lock className="absolute right-3 top-3.5 w-4 h-4 text-slate-500 group-focus-within:text-cyan-400 transition-colors" />
                    </div>
                </div>

                {/* Submit Button */}
                <Button 
                    type="submit" 
                    className="w-full h-14 mt-6 bg-white text-black hover:bg-cyan-50 font-bold tracking-[0.25em] uppercase transition-all shadow-[0_0_25px_rgba(255,255,255,0.15)] hover:shadow-[0_0_40px_rgba(6,182,212,0.3)] rounded-sm text-sm"
                    size="lg"
                >
                    Login
                </Button>

                </form>
            </CardContent>
            </Card>
            <p className="text-center text-[10px] text-slate-500 font-mono uppercase tracking-[0.3em] mt-6 opacity-70">
                USCSS Endurance • Secure Terminal v9.4
            </p>
        </div>
      </main>
    </div>
  );
};

export default InsuranceAuth;