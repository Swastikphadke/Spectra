import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { StarsBackground } from "@/components/StarsBackground";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Shield, ArrowLeft } from "lucide-react";
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
        title: "Error",
        description: "Enter a valid email",
        variant: "destructive",
      });
    }

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
      toast({ title: "OTP Sent", description: "Check your email inbox." });
    } else {
      toast({ title: "Error", description: data.error || "Failed to send OTP", variant: "destructive" });
    }
  };

  // -------------------- VERIFY OTP --------------------
  const verifyOtp = async () => {
    if (!otpValue) {
      return toast({
        title: "Error",
        description: "Enter OTP",
        variant: "destructive",
      });
    }

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
      toast({ title: "Verified", description: "Email verified successfully." });
    } else {
      toast({ title: "Error", description: data.error || "Invalid OTP", variant: "destructive" });
    }
  };

  // -------------------- FINAL SUBMIT --------------------
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.companyName || !formData.password || !formData.email) {
      return toast({
        title: "Error",
        description: "Please fill all fields",
        variant: "destructive",
      });
    }

    if (!verified) {
      return toast({
        title: "Error",
        description: "Please verify your email first",
        variant: "destructive",
      });
    }

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
      title: "Login Successful",
      description: `Welcome, ${formData.companyName}!`,
    });

    navigate("/insurance/dashboard");
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <StarsBackground />
      <Navbar />

      <main className="relative z-10 pt-24 pb-16 container mx-auto px-4">
        <Button variant="ghost" onClick={() => navigate("/")} className="mb-8">
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t("back")}
        </Button>

        <div className="max-w-md mx-auto">
          <Card variant="glass" className="animate-slide-up">
            <CardHeader className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-cosmic-purple/20 text-cosmic-purple flex items-center justify-center mx-auto mb-4">
                <Shield className="w-8 h-8" />
              </div>
              <CardTitle className="text-2xl">{t("insurance")} Portal</CardTitle>
              <CardDescription>{t("insuranceDesc")}</CardDescription>
            </CardHeader>

            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">

                {/* Company Name */}
                <div className="space-y-2">
                  <Label htmlFor="companyName">{t("companyName")}</Label>
                  <Input
                    id="companyName"
                    value={formData.companyName}
                    onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
                    placeholder="Enter company name"
                  />
                </div>

                {/* Email */}
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="Enter email"
                  />
                </div>

                {/* OTP Row */}
                <div className="flex gap-2">
                  <Button type="button" variant="outline" className="flex-1" onClick={sendOtp}>
                    Send OTP
                  </Button>
                  <Input
                    placeholder="Enter OTP"
                    value={otpValue}
                    onChange={(e) => setOtpValue(e.target.value.replace(/\D/g, "").slice(0, 6))}
                    className="w-32"
                  />
                  <Button type="button" variant="outline" onClick={verifyOtp}>
                    Verify
                  </Button>
                </div>

                {/* Password */}
                <div className="space-y-2">
                  <Label htmlFor="password">{t("password")}</Label>
                  <Input
                    id="password"
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="Enter password"
                  />
                </div>

                <Button type="submit" variant="cosmic" className="w-full" size="lg">
                  {t("signIn")}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default InsuranceAuth;
