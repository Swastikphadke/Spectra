import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { StarsBackground } from "@/components/StarsBackground";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Shield, UserPlus, LayoutDashboard, List, LogOut, CheckCircle, XCircle } from "lucide-react";
import { toast } from "@/hooks/use-toast";

// Mock data for farmers
const mockAllFarmers = [
  { id: 1, name: "Rajesh Kumar", phone: "9876543210", aadhar: "123456789012", insured: true, loanAmount: 50000 },
  { id: 2, name: "Suresh Patil", phone: "9876543211", aadhar: "123456789013", insured: false, loanAmount: 0 },
  { id: 3, name: "Mahesh Gowda", phone: "9876543212", aadhar: "123456789014", insured: true, loanAmount: 75000 },
  { id: 4, name: "Ramesh Rao", phone: "9876543213", aadhar: "123456789015", insured: false, loanAmount: 0 },
  { id: 5, name: "Ganesh Naik", phone: "9876543214", aadhar: "123456789016", insured: true, loanAmount: 100000 },
];

const InsuranceDashboard = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("add");
  const [farmers, setFarmers] = useState(mockAllFarmers);
  const [newFarmer, setNewFarmer] = useState({
    name: "",
    phone: "",
    aadhar: "",
    amount: "",
  });

  const companyName = sessionStorage.getItem("insuranceCompany") || "Insurance Co.";

  const handleAddFarmer = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newFarmer.name || !newFarmer.phone || !newFarmer.aadhar || !newFarmer.amount) {
      toast({
        title: "Error",
        description: "Please fill all fields",
        variant: "destructive",
      });
      return;
    }

    const newId = farmers.length + 1;
    setFarmers([
      ...farmers,
      {
        id: newId,
        name: newFarmer.name,
        phone: newFarmer.phone,
        aadhar: newFarmer.aadhar,
        insured: true,
        loanAmount: parseInt(newFarmer.amount),
      },
    ]);

    setNewFarmer({ name: "", phone: "", aadhar: "", amount: "" });
    
    toast({
      title: "Success",
      description: `${newFarmer.name} has been added to insurance list`,
    });
  };

  const handleLogout = () => {
    sessionStorage.removeItem("insuranceCompany");
    navigate("/");
  };

  const insuredFarmers = farmers.filter((f) => f.insured);

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <StarsBackground />
      <Navbar />
      
      <main className="relative z-10 pt-24 pb-16 container mx-auto px-4">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-display font-bold text-gradient-cosmic">
              {t("insurancePortal")}
            </h1>
            <p className="text-muted-foreground">Welcome, {companyName}</p>
          </div>
          <Button variant="outline" onClick={handleLogout}>
            <LogOut className="w-4 h-4 mr-2" />
            {t("logout")}
          </Button>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid grid-cols-3 w-full max-w-lg mx-auto bg-secondary">
            <TabsTrigger value="add" className="flex items-center gap-2">
              <UserPlus className="w-4 h-4" />
              <span className="hidden sm:inline">{t("addFarmer")}</span>
            </TabsTrigger>
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <LayoutDashboard className="w-4 h-4" />
              <span className="hidden sm:inline">{t("dashboard")}</span>
            </TabsTrigger>
            <TabsTrigger value="list" className="flex items-center gap-2">
              <List className="w-4 h-4" />
              <span className="hidden sm:inline">{t("viewInsuranceList")}</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="add">
            <Card variant="glass" className="max-w-md mx-auto">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-cosmic-purple" />
                  {t("lendInsurance")}
                </CardTitle>
                <CardDescription>Add a new farmer to your insurance coverage</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleAddFarmer} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">{t("name")}</Label>
                    <Input
                      id="name"
                      value={newFarmer.name}
                      onChange={(e) => setNewFarmer({ ...newFarmer, name: e.target.value })}
                      placeholder="Farmer's full name"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="phone">{t("phone")}</Label>
                    <Input
                      id="phone"
                      type="tel"
                      value={newFarmer.phone}
                      onChange={(e) => setNewFarmer({ ...newFarmer, phone: e.target.value.replace(/\D/g, "").slice(0, 10) })}
                      placeholder="10-digit phone number"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="aadhar">{t("aadhar")}</Label>
                    <Input
                      id="aadhar"
                      value={newFarmer.aadhar}
                      onChange={(e) => setNewFarmer({ ...newFarmer, aadhar: e.target.value.replace(/\D/g, "").slice(0, 12) })}
                      placeholder="12-digit Aadhar number"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="amount">{t("lendAmount")}</Label>
                    <Input
                      id="amount"
                      type="number"
                      value={newFarmer.amount}
                      onChange={(e) => setNewFarmer({ ...newFarmer, amount: e.target.value })}
                      placeholder="Insurance amount"
                    />
                  </div>
                  
                  <Button type="submit" variant="cosmic" className="w-full" size="lg">
                    {t("lendInsurance")}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="dashboard">
            <Card variant="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LayoutDashboard className="w-5 h-5 text-cosmic-purple" />
                  {t("allFarmers")}
                </CardTitle>
                <CardDescription>View all farmers and their insurance status</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{t("name")}</TableHead>
                        <TableHead>{t("phone")}</TableHead>
                        <TableHead>{t("aadhar")}</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>{t("amount")}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {farmers.map((farmer) => (
                        <TableRow key={farmer.id}>
                          <TableCell className="font-medium">{farmer.name}</TableCell>
                          <TableCell>{farmer.phone}</TableCell>
                          <TableCell>{farmer.aadhar}</TableCell>
                          <TableCell>
                            {farmer.insured ? (
                              <Badge className="bg-accent text-accent-foreground">
                                <CheckCircle className="w-3 h-3 mr-1" />
                                {t("insured")}
                              </Badge>
                            ) : (
                              <Badge variant="secondary">
                                <XCircle className="w-3 h-3 mr-1" />
                                {t("notInsured")}
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            {farmer.loanAmount > 0 ? `₹${farmer.loanAmount.toLocaleString()}` : "-"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="list">
            <Card variant="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <List className="w-5 h-5 text-cosmic-purple" />
                  {t("insuredFarmers")}
                </CardTitle>
                <CardDescription>Farmers currently under your insurance coverage</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{t("name")}</TableHead>
                        <TableHead>{t("phone")}</TableHead>
                        <TableHead>{t("aadhar")}</TableHead>
                        <TableHead>{t("amount")}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {insuredFarmers.map((farmer) => (
                        <TableRow key={farmer.id}>
                          <TableCell className="font-medium">{farmer.name}</TableCell>
                          <TableCell>{farmer.phone}</TableCell>
                          <TableCell>{farmer.aadhar}</TableCell>
                          <TableCell>₹{farmer.loanAmount.toLocaleString()}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default InsuranceDashboard;
