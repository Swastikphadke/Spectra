import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "@/i18n";
import Index from "./pages/Index";
import FarmerAuth from "./pages/FarmerAuth";
import InsuranceAuth from "./pages/InsuranceAuth";
import InsuranceDashboard from "./pages/InsuranceDashboard";
import BankAuth from "./pages/BankAuth";
import BankDashboard from "./pages/BankDashboard";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/farmer/auth" element={<FarmerAuth />} />
          <Route path="/insurance/auth" element={<InsuranceAuth />} />
          <Route path="/insurance/dashboard" element={<InsuranceDashboard />} />
          <Route path="/bank/auth" element={<BankAuth />} />
          <Route path="/bank/dashboard" element={<BankDashboard />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
