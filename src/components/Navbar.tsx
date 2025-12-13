import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { Satellite } from "lucide-react";
import { Link } from "react-router-dom";

export const Navbar = () => {
  const { t } = useTranslation();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass-card border-b border-border/50">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="relative">
            <div className="absolute inset-0 bg-primary/30 blur-lg rounded-full group-hover:bg-primary/50 transition-all duration-300" />
            <Satellite className="h-8 w-8 text-primary relative z-10 group-hover:rotate-12 transition-transform duration-300" />
          </div>
          <span className="font-display text-xl font-bold text-gradient-gold">
            SPECTRA
          </span>
        </Link>

        <LanguageSwitcher />
      </div>
    </nav>
  );
};
