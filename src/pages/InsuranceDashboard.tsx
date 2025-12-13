import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { StarsBackground } from "@/components/StarsBackground";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertTriangle, Calculator, FileText, BarChart3, Activity, Satellite } from "lucide-react";
import { toast } from "@/hooks/use-toast";

// --- TYPES ---
interface Farmer {
  name: string;
  phone: string;
  crop?: string;
  risk_score?: number;
}

interface Claim {
  claim_id: string;
  phone: string;
  claim_type: string;
  status: string;
  date: string;
}

const InsuranceDashboard = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const companyName = sessionStorage.getItem("insuranceCompany") || "Spectra Underwriting";

  // --- STATE ---
  const [activeTab, setActiveTab] = useState("risk");
  const [farmers, setFarmers] = useState<Farmer[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [riskFilter, setRiskFilter] = useState(false);
  
  // Feature 3: Calculator State
  const [calcData, setCalcData] = useState({ lat: "20.59", lon: "78.96", crop: "Wheat" });
  const [premiumResult, setPremiumResult] = useState<any>(null);

  // Feature 5: Analysis State
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  // --- DATA FETCHING ---
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch Farmers
        const fRes = await fetch("http://localhost:8000/api/farmers");
        const fData = await fRes.json();
        if (fData.success) setFarmers(fData.farmers);

        // Fetch Claims
        const cRes = await fetch("http://localhost:8000/api/claims");
        const cData = await cRes.json();
        if (cData.success) setClaims(cData.claims);
      } catch (e) {
        console.error("Connection Error:", e);
        toast({ title: "System Offline", description: "Could not connect to backend.", variant: "destructive" });
      }
    };
    fetchData();
  }, []);

  // --- ACTIONS ---

  // Feature 2: Smart Contract Verification
  const handleVerifyClaim = async (claimId: string, type: string) => {
    toast({ 
      title: "Initiating Orbital Scan...", 
      description: "Analyzing 30-day historical weather patterns.",
      className: "bg-black border border-cyan-500 text-cyan-400" 
    });
    
    try {
      const res = await fetch("http://localhost:8000/api/verify-claim", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ claim_id: claimId, lat: 20.0, lon: 78.0, claim_type: type })
      });
      const data = await res.json();
      
      toast({
        title: `AI VERDICT: ${data.recommendation}`,
        description: data.reason,
        className: data.recommendation === "APPROVE" 
          ? "bg-green-950 border-green-500 text-green-200" 
          : "bg-red-950 border-red-500 text-red-200"
      });
      
      // Refresh claims list to show updated status
      const cRes = await fetch("http://localhost:8000/api/claims");
      const cData = await cRes.json();
      if (cData.success) setClaims(cData.claims);

    } catch (e) { 
      toast({ title: "Signal Lost", description: "Backend unreachable.", variant: "destructive" }); 
    }
  };

  // Feature 3: Premium Calculator
  const handleCalculate = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/calculate-premium", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lat: parseFloat(calcData.lat), lon: parseFloat(calcData.lon), crop: calcData.crop })
      });
      const data = await res.json();
      setPremiumResult(data);
    } catch (e) { 
      toast({ title: "Calculation Error", variant: "destructive" }); 
    }
  };

  // Feature 5: Cluster Analysis
  const runClusterAnalysis = async () => {
    setAnalysisResult(null); // Reset UI
    try {
      const res = await fetch("http://localhost:8000/api/cluster-analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lat: 20.0, lon: 78.0 })
      });
      const data = await res.json();
      setAnalysisResult(data);
    } catch (e) { console.error(e); }
  };

  // Filter Logic
  const displayedFarmers = riskFilter ? farmers.filter(f => (f.risk_score || 0) > 70) : farmers;

  return (
    <div className="min-h-screen bg-black text-slate-200 font-sans selection:bg-cyan-500/30">
      <StarsBackground />
      <Navbar />

      <main className="relative z-10 pt-24 pb-16 container mx-auto px-4">
        
        {/* --- HEADER --- */}
        <div className="flex justify-between items-end mb-10 border-b border-white/10 pb-6 animate-in fade-in slide-in-from-top-4 duration-700">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Satellite className="w-5 h-5 text-cyan-400 animate-pulse" />
              <span className="text-[10px] font-mono text-cyan-400 tracking-[0.3em] uppercase">Spectra Systems Online</span>
            </div>
            <h1 className="text-4xl font-light text-white tracking-wide">
              Command <span className="font-bold text-amber-400">Dashboard</span>
            </h1>
            <p className="text-slate-500 mt-1 font-mono text-xs uppercase tracking-wider">
              Underwriter ID: <span className="text-slate-300">{companyName}</span>
            </p>
          </div>
          <Button 
            variant="outline" 
            className="border-white/10 bg-white/5 text-slate-400 hover:bg-red-950/30 hover:text-red-400 hover:border-red-900 transition-all font-mono text-xs" 
            onClick={() => navigate("/")}
          >
            TERMINATE SESSION
          </Button>
        </div>

        {/* --- TABS NAVIGATION --- */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-8">
          
          <TabsList className="bg-white/5 border border-white/10 p-0 rounded-none w-full justify-start h-12 backdrop-blur-md">
            <TabsTrigger value="risk" className="data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 data-[state=active]:border-b-2 data-[state=active]:border-cyan-400 rounded-none h-full px-6 text-sm font-medium tracking-widest uppercase transition-all">
              Risk Monitor
            </TabsTrigger>
            <TabsTrigger value="claims" className="data-[state=active]:bg-amber-500/10 data-[state=active]:text-amber-400 data-[state=active]:border-b-2 data-[state=active]:border-amber-400 rounded-none h-full px-6 text-sm font-medium tracking-widest uppercase transition-all">
              Smart Claims
            </TabsTrigger>
            <TabsTrigger value="premium" className="data-[state=active]:bg-purple-500/10 data-[state=active]:text-purple-400 data-[state=active]:border-b-2 data-[state=active]:border-purple-400 rounded-none h-full px-6 text-sm font-medium tracking-widest uppercase transition-all">
              Premium Calc
            </TabsTrigger>
          </TabsList>

          {/* ======================= TAB 1: LIVE RISK MONITOR ======================= */}
          <TabsContent value="risk" className="animate-in zoom-in-95 duration-300">
            <Card className="bg-black/60 border-white/10 backdrop-blur-xl shadow-2xl">
              <CardHeader className="flex flex-row items-center justify-between border-b border-white/5 pb-4">
                <div>
                  <CardTitle className="text-xl text-white font-light tracking-widest uppercase">Global Crop Health</CardTitle>
                  <CardDescription className="text-cyan-400/50 font-mono text-[10px] uppercase tracking-widest">Live Satellite Telemetry</CardDescription>
                </div>
                <div className="flex gap-3">
                  <Button 
                    variant="ghost" 
                    onClick={() => setRiskFilter(!riskFilter)}
                    className={`border font-mono text-xs ${riskFilter ? "border-red-500 text-red-400 bg-red-950/20" : "border-white/10 text-slate-400 hover:bg-white/5"}`}
                  >
                    <AlertTriangle className="w-3 h-3 mr-2" />
                    {riskFilter ? "CRITICAL ZONES" : "ALL SECTORS"}
                  </Button>
                  <Button variant="outline" className="border-white/10 text-slate-400 hover:text-white bg-transparent font-mono text-xs">
                    <FileText className="w-3 h-3 mr-2" /> EXPORT LOGS
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <Table>
                  <TableHeader>
                    <TableRow className="border-white/5 hover:bg-transparent">
                      <TableHead className="text-cyan-500/50 font-mono uppercase text-[10px] h-10">Entity Name</TableHead>
                      <TableHead className="text-cyan-500/50 font-mono uppercase text-[10px] h-10">Secure Line</TableHead>
                      <TableHead className="text-cyan-500/50 font-mono uppercase text-[10px] h-10">Asset Type</TableHead>
                      <TableHead className="text-cyan-500/50 font-mono uppercase text-[10px] h-10 w-[300px]">Health Integrity</TableHead>
                      <TableHead className="text-right text-cyan-500/50 font-mono uppercase text-[10px] h-10">Deep Scan</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {displayedFarmers.length === 0 ? (
                      <TableRow><TableCell colSpan={5} className="text-center text-slate-600 font-mono text-xs py-10">NO DATA FOUND</TableCell></TableRow>
                    ) : (
                      displayedFarmers.map((farmer, idx) => (
                      <TableRow key={idx} className="border-white/5 hover:bg-white/5 transition-colors group">
                        <TableCell className="font-medium text-slate-300 py-3">{farmer.name}</TableCell>
                        <TableCell className="font-mono text-slate-500 text-xs py-3">{farmer.phone}</TableCell>
                        <TableCell className="text-slate-400 py-3">{farmer.crop || "Unknown"}</TableCell>
                        <TableCell className="py-3">
                          <div className="flex items-center gap-3">
                            <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                              <div 
                                className={`h-full rounded-full transition-all duration-1000 ${
                                  (farmer.risk_score || 0) > 70 ? 'bg-red-500 shadow-[0_0_15px_rgba(239,68,68,0.6)]' : 'bg-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.4)]'
                                }`} 
                                style={{ width: `${farmer.risk_score}%` }} 
                              />
                            </div>
                            <span className={`font-mono text-xs w-8 text-right ${(farmer.risk_score || 0) > 70 ? 'text-red-400' : 'text-cyan-400'}`}>
                              {farmer.risk_score}%
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-right py-3">
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-cyan-500 hover:text-cyan-300 hover:bg-cyan-950/30 rounded-full" onClick={runClusterAnalysis}>
                                <Activity className="w-4 h-4" />
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="bg-black/90 border border-white/10 text-white backdrop-blur-xl sm:max-w-[600px] shadow-2xl">
                              <DialogHeader>
                                <DialogTitle className="text-amber-400 font-mono tracking-widest uppercase text-sm flex items-center gap-2">
                                  <BarChart3 className="w-4 h-4"/> Anomaly Detection
                                </DialogTitle>
                                <DialogDescription className="text-slate-500 text-xs font-mono">
                                  Comparative spectral analysis: Target vs. Proximity Cluster
                                </DialogDescription>
                              </DialogHeader>
                              {analysisResult ? (
                                <div className="space-y-6 mt-4">
                                  <div className="p-6 rounded-md bg-white/5 border border-white/10 text-center relative overflow-hidden">
                                    <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-amber-500/50 to-transparent"></div>
                                    
                                    <h4 className={`text-2xl font-bold tracking-wider mb-8 ${analysisResult.verdict === 'POSSIBLE FRAUD' ? 'text-red-500' : 'text-green-400'}`}>
                                      {analysisResult.verdict}
                                    </h4>
                                    
                                    <div className="flex items-end justify-center gap-3 h-32 pb-4 border-b border-white/5">
                                      {/* Claimant Bar */}
                                      <div className="flex flex-col items-center gap-2 group">
                                        <div className="w-10 bg-amber-600/80 border border-amber-400/50 hover:bg-amber-500 transition-all shadow-[0_0_20px_rgba(245,158,11,0.2)]" style={{ height: `${analysisResult.claimant_ndvi * 100}%` }}></div>
                                        <span className="text-[9px] font-mono text-amber-500 uppercase tracking-wider">Target</span>
                                      </div>
                                      
                                      {/* Divider */}
                                      <div className="w-px h-full bg-white/10 mx-4"></div>

                                      {/* Neighbors */}
                                      {analysisResult.neighbors.map((n: any, i: number) => (
                                        <div key={i} className="flex flex-col items-center gap-2 group">
                                          <div className="w-6 bg-cyan-900/40 border border-cyan-500/20 group-hover:bg-cyan-500/60 transition-all" style={{ height: `${n.ndvi * 100}%` }}></div>
                                          <span className="text-[9px] font-mono text-slate-600">N{i+1}</span>
                                        </div>
                                      ))}
                                    </div>
                                    <p className="text-[10px] text-slate-500 mt-4 font-mono uppercase tracking-wider">
                                      Spectral Deviation: <span className="text-white">{(analysisResult.claimant_ndvi * 100).toFixed(0)}%</span> from local baseline
                                    </p>
                                  </div>
                                  <div className="flex justify-end gap-2">
                                    <Button variant="ghost" className="text-slate-400 hover:text-white text-xs">Report False Positive</Button>
                                    <Button variant="destructive" className="bg-red-900/50 hover:bg-red-800 text-red-200 border border-red-900 text-xs">Flag for Audit</Button>
                                  </div>
                                </div>
                              ) : (
                                <div className="h-40 flex items-center justify-center flex-col gap-3">
                                  <Activity className="w-8 h-8 text-cyan-500 animate-pulse" />
                                  <p className="text-cyan-500/70 font-mono text-xs animate-pulse tracking-widest">INITIALIZING CLUSTER SCAN...</p>
                                </div>
                              )}
                            </DialogContent>
                          </Dialog>
                        </TableCell>
                      </TableRow>
                    ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ======================= TAB 2: SMART CLAIMS ======================= */}
          <TabsContent value="claims" className="animate-in zoom-in-95 duration-300">
            <Card className="bg-black/60 border-white/10 backdrop-blur-xl shadow-2xl">
              <CardHeader className="flex flex-row items-center justify-between border-b border-white/5 pb-4">
                <div>
                  <CardTitle className="text-xl text-white font-light tracking-widest uppercase">Smart Contract Queue</CardTitle>
                  <CardDescription className="text-amber-400/50 font-mono text-[10px] uppercase tracking-widest">Automated Validation Protocols</CardDescription>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <Table>
                  <TableHeader>
                    <TableRow className="border-white/5 hover:bg-transparent">
                      <TableHead className="text-amber-500/50 font-mono uppercase text-[10px] h-10">Reference ID</TableHead>
                      <TableHead className="text-amber-500/50 font-mono uppercase text-[10px] h-10">Claim Event</TableHead>
                      <TableHead className="text-amber-500/50 font-mono uppercase text-[10px] h-10">Timestamp</TableHead>
                      <TableHead className="text-amber-500/50 font-mono uppercase text-[10px] h-10">State</TableHead>
                      <TableHead className="text-right text-amber-500/50 font-mono uppercase text-[10px] h-10">Protocol</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {claims.length === 0 ? (
                      <TableRow><TableCell colSpan={5} className="text-center text-slate-600 font-mono text-xs py-10 uppercase tracking-widest">No active signals detected.</TableCell></TableRow>
                    ) : (
                      claims.map((claim, idx) => (
                        <TableRow key={idx} className="border-white/5 hover:bg-white/5 transition-colors">
                          <TableCell className="font-mono text-slate-300 text-xs py-4">{claim.claim_id}</TableCell>
                          <TableCell className="text-white py-4 flex items-center gap-2">
                            {claim.claim_type === "Drought" ? <AlertTriangle className="w-3 h-3 text-orange-500"/> : <Activity className="w-3 h-3 text-blue-500"/>}
                            {claim.claim_type}
                          </TableCell>
                          <TableCell className="text-slate-500 text-xs py-4 font-mono">{new Date(claim.date).toLocaleDateString()}</TableCell>
                          <TableCell className="py-4">
                            <Badge variant="outline" className={`border-white/10 rounded-sm font-mono text-[10px] tracking-wider ${claim.status === "Pending" ? "text-amber-400 bg-amber-950/20 animate-pulse" : "text-slate-400"}`}>
                              {claim.status.toUpperCase()}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right py-4">
                             <Button 
                               size="sm" 
                               className="h-8 bg-amber-500/10 text-amber-400 border border-amber-500/30 hover:bg-amber-500 hover:text-black transition-all font-mono text-[10px] tracking-widest uppercase w-32"
                               onClick={() => handleVerifyClaim(claim.claim_id, claim.claim_type)}
                             >
                               {claim.status === "Pending" ? "Run Verify" : "Re-Scan"}
                             </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ======================= TAB 3: PREMIUM CALCULATOR ======================= */}
          <TabsContent value="premium" className="animate-in zoom-in-95 duration-300">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              
              {/* Input Card */}
              <Card className="bg-black/60 border-white/10 backdrop-blur-xl shadow-2xl">
                <CardHeader className="border-b border-white/5 pb-4">
                  <CardTitle className="text-xl text-white font-light tracking-widest uppercase">Predictive Pricing</CardTitle>
                  <CardDescription className="text-purple-400/50 font-mono text-[10px] uppercase tracking-widest">Hyper-local Risk Modeling</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6 pt-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-slate-500 text-[10px] font-mono uppercase tracking-widest">Latitude</Label>
                      <Input 
                        value={calcData.lat} 
                        onChange={(e) => setCalcData({...calcData, lat: e.target.value})} 
                        className="bg-white/5 border-white/10 text-white font-mono focus:border-purple-500/50 focus:ring-0"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-500 text-[10px] font-mono uppercase tracking-widest">Longitude</Label>
                      <Input 
                        value={calcData.lon} 
                        onChange={(e) => setCalcData({...calcData, lon: e.target.value})} 
                        className="bg-white/5 border-white/10 text-white font-mono focus:border-purple-500/50 focus:ring-0"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-500 text-[10px] font-mono uppercase tracking-widest">Biomass Type</Label>
                    <Select onValueChange={(v) => setCalcData({...calcData, crop: v})} defaultValue={calcData.crop}>
                      <SelectTrigger className="bg-white/5 border-white/10 text-white focus:ring-purple-500/30">
                        <SelectValue placeholder="Select Crop" />
                      </SelectTrigger>
                      <SelectContent className="bg-black border-white/20 text-slate-200">
                        <SelectItem value="Wheat">Wheat</SelectItem>
                        <SelectItem value="Rice">Rice (High Water)</SelectItem>
                        <SelectItem value="Cotton">Cotton</SelectItem>
                        <SelectItem value="Sugarcane">Sugarcane</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button 
                    onClick={handleCalculate} 
                    className="w-full h-12 bg-white text-black hover:bg-purple-400 hover:text-black font-bold tracking-[0.2em] uppercase transition-all mt-4"
                  >
                    <Calculator className="w-4 h-4 mr-2" /> Init Calculation
                  </Button>
                </CardContent>
              </Card>

              {/* Result Card */}
              {premiumResult && (
                <Card className="bg-purple-950/10 border-l-2 border-l-purple-500 border-t border-b border-r border-white/5 animate-in slide-in-from-right-4 duration-500 flex flex-col justify-center">
                  <CardHeader>
                    <CardTitle className="text-4xl text-purple-400 font-mono tracking-tighter">₹{premiumResult.premium}<span className="text-lg text-slate-500 font-sans tracking-normal">/acre</span></CardTitle>
                    <CardDescription className="text-slate-400 font-mono text-xs uppercase tracking-widest">Suggested Premium Cap</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="flex justify-between items-center border-b border-white/5 pb-4">
                      <span className="text-slate-500 font-mono text-xs uppercase tracking-widest">Risk Category</span>
                      <Badge variant="outline" className={`rounded-sm px-3 py-1 font-mono text-xs tracking-wider
                        ${premiumResult.risk_level === 'High' ? 'text-red-400 border-red-500/30 bg-red-950/20' : 'text-green-400 border-green-500/30 bg-green-950/20'}
                      `}>
                        {premiumResult.risk_level.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="text-[10px] font-mono text-purple-300/70 bg-purple-900/10 p-4 rounded border border-purple-500/20">
                      &gt; {premiumResult.breakdown}
                    </div>
                    <Button variant="outline" className="w-full border-white/10 text-slate-400 hover:text-white hover:bg-white/5 font-mono text-xs uppercase tracking-widest">
                      Download Quote PDF
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

        </Tabs>
      </main>
    </div>
  );
};

export default InsuranceDashboard;