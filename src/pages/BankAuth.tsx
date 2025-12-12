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

const BankAuth = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    id: "",
    password: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.id || !formData.password) {
      toast({
        title: "Error",
        description: "Please fill all fields",
        variant: "destructive",
      });
      return;
    }

    // Store bank ID in sessionStorage for demo
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
              <div className="w-16 h-16 rounded-2xl bg-earth-green/20 text-earth-green flex items-center justify-center mx-auto mb-4">
                <Building2 className="w-8 h-8" />
              </div>
              <CardTitle className="text-2xl">{t("bank")} Portal</CardTitle>
              <CardDescription>{t("bankDesc")}</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="id">{t("id")}</Label>
                  <Input
                    id="id"
                    value={formData.id}
                    onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                    placeholder="Enter bank ID"
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
