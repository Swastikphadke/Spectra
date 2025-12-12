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
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Building2, Search, LayoutDashboard, Banknote, LogOut, CheckCircle, XCircle, IndianRupee } from "lucide-react";
import { toast } from "@/hooks/use-toast";

// Mock data for farmers
const mockFarmers = [
  { id: 1, name: "Rajesh Kumar", phone: "9876543210", aadhar: "123456789012", bankAccount: "SBI12345678", insured: true, hasLoan: false, loanAmount: 0 },
  { id: 2, name: "Suresh Patil", phone: "9876543211", aadhar: "123456789013", bankAccount: "BOB12345678", insured: false, hasLoan: true, loanAmount: 25000 },
  { id: 3, name: "Mahesh Gowda", phone: "9876543212", aadhar: "123456789014", bankAccount: "HDFC12345678", insured: true, hasLoan: false, loanAmount: 0 },
  { id: 4, name: "Ramesh Rao", phone: "9876543213", aadhar: "123456789015", bankAccount: "ICICI12345678", insured: false, hasLoan: false, loanAmount: 0 },
  { id: 5, name: "Ganesh Naik", phone: "9876543214", aadhar: "123456789016", bankAccount: "AXIS12345678", insured: true, hasLoan: true, loanAmount: 50000 },
];

const BankDashboard = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("search");
  const [farmers, setFarmers] = useState(mockFarmers);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<typeof mockFarmers>([]);
  const [selectedFarmer, setSelectedFarmer] = useState<typeof mockFarmers[0] | null>(null);
  const [loanAmount, setLoanAmount] = useState("");
  const [isLoanDialogOpen, setIsLoanDialogOpen] = useState(false);

  const bankId = sessionStorage.getItem("bankId") || "BANK001";

  const handleSearch = () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    const query = searchQuery.toLowerCase();
    const results = farmers.filter(
      (f) =>
        f.name.toLowerCase().includes(query) ||
        f.phone.includes(query) ||
        f.aadhar.includes(query)
    );
    setSearchResults(results);
  };

  const handleProcessLoan = () => {
    if (!selectedFarmer || !loanAmount) {
      toast({
        title: "Error",
        description: "Please enter loan amount",
        variant: "destructive",
      });
      return;
    }

    const amount = parseInt(loanAmount);
    if (isNaN(amount) || amount <= 0) {
      toast({
        title: "Error",
        description: "Please enter a valid amount",
        variant: "destructive",
      });
      return;
    }

    setFarmers(
      farmers.map((f) =>
        f.id === selectedFarmer.id
          ? { ...f, hasLoan: true, loanAmount: f.loanAmount + amount }
          : f
      )
    );

    toast({
      title: "Loan Processed",
      description: `₹${amount.toLocaleString()} has been credited to ${selectedFarmer.name}'s account (${selectedFarmer.bankAccount})`,
    });

    setIsLoanDialogOpen(false);
    setSelectedFarmer(null);
    setLoanAmount("");
    setSearchResults([]);
    setSearchQuery("");
  };

  const handleLogout = () => {
    sessionStorage.removeItem("bankId");
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <StarsBackground />
      <Navbar />
      
      <main className="relative z-10 pt-24 pb-16 container mx-auto px-4">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-display font-bold text-accent">
              {t("bankPortal")}
            </h1>
            <p className="text-muted-foreground">Bank ID: {bankId}</p>
          </div>
          <Button variant="outline" onClick={handleLogout}>
            <LogOut className="w-4 h-4 mr-2" />
            {t("logout")}
          </Button>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid grid-cols-3 w-full max-w-lg mx-auto bg-secondary">
            <TabsTrigger value="search" className="flex items-center gap-2">
              <Search className="w-4 h-4" />
              <span className="hidden sm:inline">{t("searchFarmer")}</span>
            </TabsTrigger>
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <LayoutDashboard className="w-4 h-4" />
              <span className="hidden sm:inline">{t("dashboard")}</span>
            </TabsTrigger>
            <TabsTrigger value="loan" className="flex items-center gap-2">
              <Banknote className="w-4 h-4" />
              <span className="hidden sm:inline">{t("giveLoan")}</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="search">
            <Card variant="glass" className="max-w-2xl mx-auto">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Search className="w-5 h-5 text-earth-green" />
                  {t("searchFarmer")}
                </CardTitle>
                <CardDescription>{t("searchBy")}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-4">
                  <Input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder={t("searchBy")}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  />
                  <Button variant="earth" onClick={handleSearch}>
                    <Search className="w-4 h-4 mr-2" />
                    {t("search")}
                  </Button>
                </div>

                {searchResults.length > 0 && (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>{t("name")}</TableHead>
                          <TableHead>{t("phone")}</TableHead>
                          <TableHead>{t("aadhar")}</TableHead>
                          <TableHead>Insurance</TableHead>
                          <TableHead>Loan</TableHead>
                          <TableHead>Action</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {searchResults.map((farmer) => (
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
                              {farmer.hasLoan ? (
                                <span className="text-primary">₹{farmer.loanAmount.toLocaleString()}</span>
                              ) : (
                                <span className="text-muted-foreground">{t("noLoan")}</span>
                              )}
                            </TableCell>
                            <TableCell>
                              <Dialog open={isLoanDialogOpen && selectedFarmer?.id === farmer.id} onOpenChange={(open) => {
                                setIsLoanDialogOpen(open);
                                if (open) setSelectedFarmer(farmer);
                              }}>
                                <DialogTrigger asChild>
                                  <Button variant="earth" size="sm">
                                    <IndianRupee className="w-4 h-4 mr-1" />
                                    {t("giveLoan")}
                                  </Button>
                                </DialogTrigger>
                                <DialogContent className="bg-card border-border">
                                  <DialogHeader>
                                    <DialogTitle>{t("processLoan")}</DialogTitle>
                                    <DialogDescription>
                                      Process loan for {farmer.name} (Account: {farmer.bankAccount})
                                    </DialogDescription>
                                  </DialogHeader>
                                  <div className="space-y-4">
                                    <div className="space-y-2">
                                      <Label>{t("loanAmount")}</Label>
                                      <Input
                                        type="number"
                                        value={loanAmount}
                                        onChange={(e) => setLoanAmount(e.target.value)}
                                        placeholder="Enter loan amount"
                                      />
                                    </div>
                                  </div>
                                  <DialogFooter>
                                    <Button variant="outline" onClick={() => setIsLoanDialogOpen(false)}>
                                      {t("cancel")}
                                    </Button>
                                    <Button variant="earth" onClick={handleProcessLoan}>
                                      {t("processLoan")}
                                    </Button>
                                  </DialogFooter>
                                </DialogContent>
                              </Dialog>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}

                {searchQuery && searchResults.length === 0 && (
                  <p className="text-center text-muted-foreground py-8">No farmers found matching your search</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="dashboard">
            <Card variant="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LayoutDashboard className="w-5 h-5 text-earth-green" />
                  {t("allFarmers")}
                </CardTitle>
                <CardDescription>View all farmers and their financial status</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{t("name")}</TableHead>
                        <TableHead>{t("phone")}</TableHead>
                        <TableHead>{t("aadhar")}</TableHead>
                        <TableHead>{t("bankAccount")}</TableHead>
                        <TableHead>Insurance</TableHead>
                        <TableHead>Loan Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {farmers.map((farmer) => (
                        <TableRow key={farmer.id}>
                          <TableCell className="font-medium">{farmer.name}</TableCell>
                          <TableCell>{farmer.phone}</TableCell>
                          <TableCell>{farmer.aadhar}</TableCell>
                          <TableCell>{farmer.bankAccount}</TableCell>
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
                            {farmer.hasLoan ? (
                              <Badge className="bg-primary text-primary-foreground">
                                ₹{farmer.loanAmount.toLocaleString()}
                              </Badge>
                            ) : (
                              <span className="text-muted-foreground">{t("noLoan")}</span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="loan">
            <Card variant="glass" className="max-w-2xl mx-auto">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Banknote className="w-5 h-5 text-earth-green" />
                  {t("giveLoan")}
                </CardTitle>
                <CardDescription>Search for a farmer to process their loan</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-4">
                  <Input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder={t("searchBy")}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  />
                  <Button variant="earth" onClick={handleSearch}>
                    <Search className="w-4 h-4 mr-2" />
                    {t("search")}
                  </Button>
                </div>

                {searchResults.length > 0 && (
                  <div className="space-y-4">
                    {searchResults.map((farmer) => (
                      <Card key={farmer.id} variant="glass" className="p-4">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                          <div>
                            <h3 className="font-display font-semibold text-lg">{farmer.name}</h3>
                            <p className="text-sm text-muted-foreground">
                              {farmer.phone} | {farmer.aadhar}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              Account: {farmer.bankAccount}
                            </p>
                            <div className="flex gap-2 mt-2">
                              {farmer.insured ? (
                                <Badge className="bg-accent text-accent-foreground">{t("insured")}</Badge>
                              ) : (
                                <Badge variant="secondary">{t("notInsured")}</Badge>
                              )}
                              {farmer.hasLoan && (
                                <Badge className="bg-primary text-primary-foreground">
                                  Loan: ₹{farmer.loanAmount.toLocaleString()}
                                </Badge>
                              )}
                            </div>
                          </div>
                          <div className="flex gap-2 items-end">
                            <Input
                              type="number"
                              placeholder="Amount (₹)"
                              className="w-32"
                              value={selectedFarmer?.id === farmer.id ? loanAmount : ""}
                              onChange={(e) => {
                                setSelectedFarmer(farmer);
                                setLoanAmount(e.target.value);
                              }}
                            />
                            <Button
                              variant="earth"
                              onClick={() => {
                                setSelectedFarmer(farmer);
                                handleProcessLoan();
                              }}
                              disabled={selectedFarmer?.id !== farmer.id || !loanAmount}
                            >
                              <IndianRupee className="w-4 h-4 mr-1" />
                              {t("processLoan")}
                            </Button>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}

                {searchQuery && searchResults.length === 0 && (
                  <p className="text-center text-muted-foreground py-8">No farmers found matching your search</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default BankDashboard;
