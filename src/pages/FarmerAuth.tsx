import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { StarsBackground } from "@/components/StarsBackground";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Tractor, ArrowLeft, MessageCircle, CheckCircle2 } from "lucide-react";
import { toast } from "@/hooks/use-toast";

const FarmerAuth = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    aadhar: "",
    bankAccount: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.phone || !formData.aadhar || !formData.bankAccount) {
      toast({
        title: "Error",
        description: "Please fill all fields",
        variant: "destructive",
      });
      return;
    }

    if (!/^\d{10}$/.test(formData.phone)) {
      toast({
        title: "Error",
        description: "Please enter a valid 10-digit phone number",
        variant: "destructive",
      });
      return;
    }

    if (!/^\d{12}$/.test(formData.aadhar)) {
      toast({
        title: "Error",
        description: "Please enter a valid 12-digit Aadhar number",
        variant: "destructive",
      });
      return;
    }

    // ⭐ SEND TO BACKEND JSON STORAGE
    await fetch("http://localhost:5000/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        role: "farmer",
        ...formData,
        timestamp: new Date().toISOString(),
      }),
    });

    setIsSubmitted(true);
    toast({
      title: "Registration Successful",
      description: "Please share your location on WhatsApp",
    });
  };

  const handleWhatsAppShare = () => {
    const message = encodeURIComponent(
      `Hello! I am ${formData.name}. I have registered on AgroSat. Here is my farm location:`
    );
    window.open(`https://wa.me/?text=${message}`, "_blank");
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
          {!isSubmitted ? (
            <Card variant="glass" className="animate-slide-up">
              <CardHeader className="text-center">
                <div className="w-16 h-16 rounded-2xl bg-earth-gold/20 text-earth-gold flex items-center justify-center mx-auto mb-4">
                  <Tractor className="w-8 h-8" />
                </div>
                <CardTitle className="text-2xl">{t("farmerSignup")}</CardTitle>
                <CardDescription>{t("farmerDesc")}</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">{t("name")}</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Enter your full name"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="phone">{t("phone")}</Label>
                    <Input
                      id="phone"
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value.replace(/\D/g, "").slice(0, 10) })}
                      placeholder="10-digit phone number"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="aadhar">{t("aadhar")}</Label>
                    <Input
                      id="aadhar"
                      value={formData.aadhar}
                      onChange={(e) => setFormData({ ...formData, aadhar: e.target.value.replace(/\D/g, "").slice(0, 12) })}
                      placeholder="12-digit Aadhar number"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="bankAccount">{t("bankAccount")}</Label>
                    <Input
                      id="bankAccount"
                      value={formData.bankAccount}
                      onChange={(e) => setFormData({ ...formData, bankAccount: e.target.value })}
                      placeholder="Bank account number"
                    />
                  </div>
                  
                  <Button type="submit" variant="gold" className="w-full" size="lg">
                    {t("submit")}
                  </Button>
                </form>
              </CardContent>
            </Card>
          ) : (
            <Card variant="glass" className="animate-slide-up text-center">
              <CardHeader>
                <div className="w-20 h-20 rounded-full bg-accent/20 text-accent flex items-center justify-center mx-auto mb-4 animate-pulse-glow">
                  <CheckCircle2 className="w-10 h-10" />
                </div>
                <CardTitle className="text-2xl text-accent">Registration Complete!</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <p className="text-muted-foreground">{t("whatsappMessage")}</p>
                
                <Button variant="earth" size="lg" className="w-full" onClick={handleWhatsAppShare}>
                  <MessageCircle className="w-5 h-5 mr-2" />
                  {t("shareLocation")}
                </Button>
                
                <Button variant="outline" onClick={() => navigate("/")} className="w-full">
                  {t("back")} {t("home")}
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
};

export default FarmerAuth;
