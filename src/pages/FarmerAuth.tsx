import { useState, useMemo, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { StarsBackground } from "@/components/StarsBackground";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Tractor, ArrowLeft, MessageCircle, CheckCircle2, MapPin, Search } from "lucide-react";
import { toast } from "@/hooks/use-toast";

// --- LEAFLET IMPORTS ---
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// --- LEAFLET ICON FIX ---
import icon from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";

const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

// --- MAP HELPER COMPONENTS ---

// 1. Component to move the map view
const RecenterAutomatically = ({ lat, lng }: { lat: number; lng: number }) => {
  const map = useMap();
  useEffect(() => {
    map.flyTo([lat, lng], 13); // Zoom level 13 is better for finding towns
  }, [lat, lng, map]);
  return null;
};

// 2. Component for the Draggable Marker
const DraggableMarker = ({ position, setPosition }: { position: { lat: number; lng: number }, setPosition: (lat: number, lng: number) => void }) => {
  const markerRef = useRef<L.Marker>(null);

  const eventHandlers = useMemo(
    () => ({
      dragend() {
        const marker = markerRef.current;
        if (marker != null) {
          const { lat, lng } = marker.getLatLng();
          setPosition(lat, lng);
        }
      },
    }),
    [setPosition]
  );

  return (
    <Marker
      draggable={true}
      eventHandlers={eventHandlers}
      position={position}
      ref={markerRef}
    >
      <Popup>Drag me to your plot location!</Popup>
    </Marker>
  );
};

const FarmerAuth = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [searchQuery, setSearchQuery] = useState(""); // State for search input
  const [isSearching, setIsSearching] = useState(false);
  
  // Default map center (India center approx)
  const defaultCenter = { lat: 20.5937, lng: 78.9629 };

  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    aadhar: "",
    bankAccount: "",
    crop: "",
    lat: "", 
    long: "",
  });

  const getLanguageName = (code: string) => {
    const langMap: Record<string, string> = {
      'en': 'English', 'hi': 'Hindi', 'kn': 'Kannada', 'te': 'Telugu', 'ta': 'Tamil'
    };
    return langMap[code] || code.charAt(0).toUpperCase() + code.slice(1);
  };

  // --- NEW SEARCH FUNCTION ---
  const handleSearchLocation = async () => {
    if (!searchQuery) return;
    setIsSearching(true);

    try {
      // Using OpenStreetMap Nominatim API (Free)
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}`
      );
      const data = await response.json();

      if (data && data.length > 0) {
        const { lat, lon } = data[0];
        setFormData((prev) => ({
          ...prev,
          lat: parseFloat(lat).toFixed(6),
          long: parseFloat(lon).toFixed(6),
        }));
        toast({
          title: "Location Found",
          description: `Map moved to ${searchQuery}`,
        });
      } else {
        toast({
          title: "Not Found",
          description: "Could not find that place or pincode.",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to search location.",
        variant: "destructive",
      });
    } finally {
      setIsSearching(false);
    }
  };

  const handleGetLocation = () => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude.toFixed(6);
          const long = position.coords.longitude.toFixed(6);
          
          setFormData(prev => ({
            ...prev,
            lat: lat,
            long: long
          }));
          
          toast({
            title: "Location Detected",
            description: "Map updated to your current location.",
          });
        },
        (error) => {
          toast({
            title: "Location Error",
            description: "Could not fetch location.",
            variant: "destructive",
          });
        }
      );
    } else {
      toast({
        title: "Not Supported",
        description: "Geolocation is not supported by your browser.",
        variant: "destructive",
      });
    }
  };

  const handleMarkerDrag = (lat: number, lng: number) => {
    setFormData(prev => ({
      ...prev,
      lat: lat.toFixed(6),
      long: lng.toFixed(6)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.phone || !formData.aadhar || !formData.bankAccount) {
      toast({ title: "Error", description: "Please fill all mandatory fields", variant: "destructive" });
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role: "farmer",
          name: formData.name,
          phone_number: formData.phone,
          aadhar: formData.aadhar,
          bank_acc: formData.bankAccount,
          crop: formData.crop || null,
          lat: formData.lat ? parseFloat(formData.lat) : null,
          long: formData.long ? parseFloat(formData.long) : null,
          language: getLanguageName(i18n.language), 
          timestamp: new Date().toISOString(),
        }),
      });

      if (!response.ok) throw new Error("Registration failed");
      setIsSubmitted(true);
      toast({ title: "Registration Successful", description: "Profile created successfully!" });
    } catch (error) {
      console.error("Error registering:", error);
      toast({ title: "Registration Failed", description: "Could not connect to server.", variant: "destructive" });
    }
  };

  const handleWhatsAppShare = () => {
    const message = encodeURIComponent(`Hello! I am ${formData.name}. I have registered on AgroSat.`);
    window.open(`https://wa.me/?text=${message}`, "_blank");
  };

  const mapCenter = (formData.lat && formData.long) 
    ? { lat: parseFloat(formData.lat), lng: parseFloat(formData.long) } 
    : defaultCenter;

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
                  <div className="space-y-2"><Label htmlFor="name">{t("name")} *</Label><Input id="name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder="Enter full name" /></div>
                  <div className="space-y-2"><Label htmlFor="phone">{t("phone")} *</Label><Input id="phone" type="tel" value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value.replace(/\D/g, "").slice(0, 10) })} placeholder="10-digit phone" /></div>
                  <div className="space-y-2"><Label htmlFor="aadhar">{t("aadhar")} *</Label><Input id="aadhar" value={formData.aadhar} onChange={(e) => setFormData({ ...formData, aadhar: e.target.value.replace(/\D/g, "").slice(0, 12) })} placeholder="12-digit Aadhar" /></div>
                  <div className="space-y-2"><Label htmlFor="bankAccount">{t("bankAccount")} *</Label><Input id="bankAccount" value={formData.bankAccount} onChange={(e) => setFormData({ ...formData, bankAccount: e.target.value })} placeholder="Bank account" /></div>
                  <div className="space-y-2"><Label htmlFor="crop">Crop Type (Optional)</Label><Input id="crop" value={formData.crop} onChange={(e) => setFormData({ ...formData, crop: e.target.value })} placeholder="e.g. Wheat, Rice" /></div>

                  {/* --- MAP SECTION START --- */}
                  <div className="space-y-3">
                    <Label>Farm Location</Label>

                    {/* NEW: Search Bar */}
                    <div className="flex gap-2">
                      <Input 
                        placeholder="Enter Pincode or City Name" 
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleSearchLocation())}
                      />
                      <Button type="button" variant="outline" onClick={handleSearchLocation} disabled={isSearching}>
                        {isSearching ? "..." : <Search className="w-4 h-4" />}
                      </Button>
                    </div>
                    
                    {/* The Map */}
                    <div className="h-[300px] w-full rounded-md overflow-hidden border border-input">
                      <MapContainer 
                        center={[mapCenter.lat, mapCenter.lng]} 
                        zoom={5} 
                        scrollWheelZoom={true} 
                        style={{ height: "100%", width: "100%" }}
                      >
                        <TileLayer
                          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        />
                        <RecenterAutomatically lat={mapCenter.lat} lng={mapCenter.lng} />
                        <DraggableMarker position={mapCenter} setPosition={handleMarkerDrag} />
                      </MapContainer>
                    </div>

                    {/* Button to get GPS */}
                    <Button 
                      type="button" 
                      variant="outline" 
                      className="w-full"
                      onClick={handleGetLocation}
                    >
                      <MapPin className="w-4 h-4 mr-2" />
                      Get Current Location
                    </Button>

                    {/* Manual Inputs */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="lat">Latitude</Label>
                        <Input
                          id="lat"
                          value={formData.lat}
                          onChange={(e) => setFormData({ ...formData, lat: e.target.value })}
                          placeholder="0.00"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="long">Longitude</Label>
                        <Input
                          id="long"
                          value={formData.long}
                          onChange={(e) => setFormData({ ...formData, long: e.target.value })}
                          placeholder="0.00"
                        />
                      </div>
                    </div>
                  </div>
                  {/* --- MAP SECTION END --- */}

                  <Button type="submit" variant="gold" className="w-full" size="lg">
                    {t("submit")}
                  </Button>
                </form>
              </CardContent>
            </Card>
          ) : (
             <Card variant="glass" className="animate-slide-up text-center">
              <CardHeader>
                <div className="w-20 h-20 rounded-full bg-accent/20 text-accent flex items-center justify-center mx-auto mb-4 animate-pulse-glow"><CheckCircle2 className="w-10 h-10" /></div>
                <CardTitle className="text-2xl text-accent">Registration Complete!</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <p className="text-muted-foreground">{t("whatsappMessage")}</p>
                <Button variant="earth" size="lg" className="w-full" onClick={handleWhatsAppShare}><MessageCircle className="w-5 h-5 mr-2" />{t("shareLocation")}</Button>
                <Button variant="outline" onClick={() => navigate("/")} className="w-full">{t("back")} {t("home")}</Button>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
};

export default FarmerAuth;