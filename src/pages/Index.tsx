import { useTranslation } from "react-i18next";
import { Navbar } from "@/components/Navbar";
import { StarsBackground } from "@/components/StarsBackground";
import { RoleCard } from "@/components/RoleCard";
import { Tractor, Shield, Building2, Satellite, Leaf, Globe2 } from "lucide-react";

// ✨ Particles
import Particles from "react-tsparticles";
import { loadFull } from "tsparticles";
import { useCallback } from "react";

const Index = () => {
  const { t } = useTranslation();

  // Initialize particles
  const particlesInit = useCallback(async (engine) => {
    await loadFull(engine);
  }, []);

  return (
    <div className="min-h-screen relative overflow-hidden bg-transparent">

      {/* 🌌 PARTICLES ABOVE STARS BUT BELOW UI */}
      <Particles
        id="tsparticles"
        init={particlesInit}
        className="fixed inset-0 z-0"
        options={{
          background: { color: "transparent" },
          particles: {
            number: { value: 150 },
            size: { value: 3 },
            color: { value: "#ffffff" },
            move: { speed: 0.6 },
            opacity: { value: 0.9 },
          },
        }}
      />

      {/* ⭐ STAR BACKGROUND BELOW PARTICLES */}
      <StarsBackground />

      {/* 🌀 ORBITAL RINGS BELOW BOTH */}
      <div
        className="absolute -z-10 top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2
        w-[800px] h-[800px] border border-border/20 rounded-full animate-spin"
        style={{ animationDuration: "60s" }}
      />
      <div
        className="absolute -z-10 top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2
        w-[600px] h-[600px] border border-primary/10 rounded-full animate-spin"
        style={{ animationDuration: "40s", animationDirection: "reverse" }}
      />

      <Navbar />

      <main className="relative z-10 pt-24 pb-16">
        {/* HERO SECTION */}
        <section className="container mx-auto px-4 text-center py-16">
          <div className="max-w-4xl mx-auto">
            <div className="relative inline-block mb-8 animate-float">
              <div className="absolute inset-0 bg-primary/30 blur-2xl rounded-full" />
              <div className="relative bg-card/50 backdrop-blur-xl p-6 rounded-full border border-border/50">
                <Satellite className="w-16 h-16 text-primary" />
              </div>
            </div>

            <p className="text-primary font-medium mb-4 tracking-widest uppercase opacity-0 animate-slide-up stagger-1">
              {t("heroSubtitle")}
            </p>

            <h1 className="text-5xl md:text-7xl font-display font-bold mb-6 opacity-0 animate-slide-up stagger-2">
              <span className="text-gradient-gold">{t("heroTitle")}</span>
            </h1>

            <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-12 opacity-0 animate-slide-up stagger-3">
              {t("heroDescription")}
            </p>

            {/* FEATURE HIGHLIGHTS */}
            <div className="flex flex-wrap justify-center gap-6 mb-16 opacity-0 animate-slide-up stagger-4">
              <div className="flex items-center gap-2 glass-card px-4 py-2 rounded-full">
                <Satellite className="w-5 h-5 text-primary" />
                <span className="text-sm">Real-time Data</span>
              </div>
              <div className="flex items-center gap-2 glass-card px-4 py-2 rounded-full">
                <Leaf className="w-5 h-5 text-accent" />
                <span className="text-sm">Crop Insights</span>
              </div>
              <div className="flex items-center gap-2 glass-card px-4 py-2 rounded-full">
                <Globe2 className="w-5 h-5 text-cosmic-blue" />
                <span className="text-sm">Weather Forecasts</span>
              </div>
            </div>
          </div>
        </section>

        {/* ROLE SELECTION SECTION */}
        <section className="container mx-auto px-4 py-8">
          <h2 className="text-3xl font-display font-bold text-center mb-12 opacity-0 animate-slide-up stagger-5">
            {t("selectRole")}
          </h2>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <RoleCard
              icon={Tractor}
              title={t("farmer")}
              description={t("farmerDesc")}
              path="/farmer/auth"
              gradient="gold"
              delay={600}
            />
            <RoleCard
              icon={Shield}
              title={t("insurance")}
              description={t("insuranceDesc")}
              path="/insurance/auth"
              gradient="cosmic"
              delay={700}
            />
            <RoleCard
              icon={Building2}
              title={t("bank")}
              description={t("bankDesc")}
              path="/bank/auth"
              gradient="earth"
              delay={800}
            />
          </div>
        </section>
      </main>

      <footer className="relative z-10 border-t border-border/50 py-8">
        <div className="container mx-auto px-4 text-center text-muted-foreground text-sm">
          <p>© 2024 AgroSat - Satellite-Powered Farming Solutions</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
