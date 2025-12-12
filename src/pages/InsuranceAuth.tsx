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

const InsuranceAuth = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    companyName: "",
    password: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.companyName || !formData.password) {
      toast({
        title: "Error",
        description: "Please fill all fields",
        variant: "destructive",
      });
      return;
    }

    // Store company name in sessionStorage for demo
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
        <Button
          variant="ghost"
          onClick={() => navigate("/")}
          className="mb-8"
        >
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
                <div className="space-y-2">
                  <Label htmlFor="companyName">{t("companyName")}</Label>
                  <Input
                    id="companyName"
                    value={formData.companyName}
                    onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
                    placeholder="Enter company name"
                  />
                </div>
                
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
