import { LucideIcon } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

interface RoleCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  path: string;
  gradient: "gold" | "cosmic" | "earth";
  delay?: number;
}

export const RoleCard = ({ icon: Icon, title, description, path, gradient, delay = 0 }: RoleCardProps) => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const gradientClasses = {
    gold: "from-earth-gold/20 to-earth-gold/5 hover:from-earth-gold/30 hover:to-earth-gold/10 border-earth-gold/30",
    cosmic: "from-cosmic-purple/20 to-cosmic-blue/5 hover:from-cosmic-purple/30 hover:to-cosmic-blue/10 border-cosmic-purple/30",
    earth: "from-earth-green/20 to-earth-green/5 hover:from-earth-green/30 hover:to-earth-green/10 border-earth-green/30",
  };

  const iconBgClasses = {
    gold: "bg-earth-gold/20 text-earth-gold",
    cosmic: "bg-cosmic-purple/20 text-cosmic-purple",
    earth: "bg-earth-green/20 text-earth-green",
  };

  const buttonVariants = {
    gold: "gold" as const,
    cosmic: "cosmic" as const,
    earth: "earth" as const,
  };

  return (
    <Card
      className={`relative overflow-hidden bg-gradient-to-br ${gradientClasses[gradient]} backdrop-blur-xl cursor-pointer group opacity-0 animate-slide-up`}
      style={{ animationDelay: `${delay}ms`, animationFillMode: "forwards" }}
      onClick={() => navigate(path)}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-transparent to-background/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      
      <CardHeader className="relative z-10">
        <div className={`w-16 h-16 rounded-2xl ${iconBgClasses[gradient]} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
          <Icon className="w-8 h-8" />
        </div>
        <CardTitle className="text-xl">{title}</CardTitle>
        <CardDescription className="text-muted-foreground">{description}</CardDescription>
      </CardHeader>
      
      <CardContent className="relative z-10">
        <Button variant={buttonVariants[gradient]} className="w-full" size="lg">
          {t("signIn")} / {t("signUp")}
        </Button>
      </CardContent>
    </Card>
  );
};
