import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { StarsBackground } from "@/components/StarsBackground";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Building2, ArrowLeft } from "lucide-react";
import { toast } from "@/hooks/use-toast";

const API_BASE = "http://localhost:8000"; // backend URL

const BankAuth = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    id: "",
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
        role: "bank",
      }),
    });

    const data = await res.json();

    if (data.success) {
      setOtpSent(true);
      toast({ title: "OTP Sent", description: "Check your inbox for OTP." });
    } else {
      toast({
        title: "Error",
        description: data.error || "Failed to send OTP",
        variant: "destructive",
      });
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
      toast({
        title: "Error",
        description: data.error || "Invalid OTP",
        variant: "destructive",
      });
    }
  };

  // -------------------- FINAL LOGIN SUBMIT --------------------
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.id || !formData.password || !formData.email) {
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

    await fetch(`${API_BASE}/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        role: "bank",
        id: formData.id,
        password: formData.password,
        email: formData.email,
        emailVerified: true,
        timestamp: new Date().toISOString(),
      }),
    });

    // Store bank ID
    sessionStorage.setItem("bankId", formData.id);

    toast({
      title: "Login Successful",
      description: `Welcome, Bank ID: ${formData.id}!`,
    });

    navigate("/bank/dashboard");
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
              <div className="w-16 h-16 rounded-2xl bg-earth-green/20 text-earth-green flex items-center justify-center mx-auto mb-4">
                <Building2 className="w-8 h-8" />
              </div>
              <CardTitle className="text-2xl">{t("bank")} Portal</CardTitle>
              <CardDescription>{t("bankDesc")}</CardDescription>
            </CardHeader>

            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">

                {/* Bank ID */}
                <div className="space-y-2">
                  <Label htmlFor="id">{t("id")}</Label>
                  <Input
                    id="id"
                    value={formData.id}
                    onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                    placeholder="Enter bank ID"
                  />
                </div>

                {/* Email Input */}
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="Enter email"
                  />
                </div>

                {/* OTP Section */}
                <div className="flex gap-2">
                  <Button type="button" variant="outline" className="flex-1" onClick={sendOtp}>
                    Send OTP
                  </Button>

                  <Input
                    placeholder="OTP"
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

                <Button type="submit" variant="earth" className="w-full" size="lg">
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

export default BankAuth;
