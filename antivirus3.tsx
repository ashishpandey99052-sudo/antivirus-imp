import { useState, useEffect } from "react";
import { Dashboard } from "@/components/Dashboard";
import { Scanner } from "@/components/Scanner";
import { ThreatList } from "@/components/ThreatList";
import { Shield } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Threat {
  id: string;
  name: string;
  path: string;
  severity: "high" | "medium" | "low";
  type: string;
}

const Index = () => {
  const [securityStatus, setSecurityStatus] = useState<"protected" | "threats" | "scanning">("protected");
  const [threatsFound, setThreatsFound] = useState(0);
  const [filesScanned, setFilesScanned] = useState(12547);
  const [lastScan, setLastScan] = useState("2 hours ago");
  const [threats, setThreats] = useState<Threat[]>([]);
  const { toast } = useToast();

  const mockThreats: Threat[] = [
    {
      id: "1",
      name: "Trojan.Win32.Generic",
      path: "C:\\Program Files\\Common\\malware.exe",
      severity: "high",
      type: "Trojan Horse",
    },
    {
      id: "2",
      name: "Adware.PUP.Optional",
      path: "C:\\Users\\Downloads\\crack_software.zip",
      severity: "medium",
      type: "Potentially Unwanted Program",
    },
    {
      id: "3",
      name: "Ransomware.Detected",
      path: "C:\\Users\\Documents\\invoice.pdf.exe",
      severity: "high",
      type: "Ransomware",
    },
  ];

  const handleScanStart = () => {
    setSecurityStatus("scanning");
    setThreats([]);
  };

  const handleScanComplete = (newThreats: number, scannedFiles: number) => {
    setFilesScanned((prev) => prev + scannedFiles);
    setLastScan("Just now");

    if (newThreats > 0) {
      setThreatsFound(newThreats);
      setSecurityStatus("threats");
      setThreats(mockThreats.slice(0, newThreats));
      toast({
        title: "Scan Complete",
        description: `Found ${newThreats} threat${newThreats !== 1 ? 's' : ''}. Please review and quarantine.`,
        variant: "destructive",
      });
    } else {
      setSecurityStatus("protected");
      toast({
        title: "Scan Complete",
        description: "No threats detected. Your system is secure.",
      });
    }
  };

  const handleQuarantine = (threatId: string) => {
    setThreats((prev) => prev.filter((t) => t.id !== threatId));
    setThreatsFound((prev) => Math.max(0, prev - 1));
    
    toast({
      title: "Threat Quarantined",
      description: "The threat has been successfully isolated and removed.",
    });

    // Update status if no more threats
    setTimeout(() => {
      if (threats.length <= 1) {
        setSecurityStatus("protected");
      }
    }, 100);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card shadow-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary rounded-lg">
              <Shield className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">SecureGuard Antivirus</h1>
              <p className="text-sm text-muted-foreground">Real-time protection & threat detection</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8 max-w-7xl mx-auto">
          <Dashboard
            securityStatus={securityStatus}
            threatsFound={threatsFound}
            filesScanned={filesScanned}
            lastScan={lastScan}
          />

          <Scanner
            onScanComplete={handleScanComplete}
            onScanStart={handleScanStart}
          />

          <ThreatList threats={threats} onQuarantine={handleQuarantine} />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t mt-16 py-6">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>SecureGuard Antivirus • Version 2.0 • Real-time Protection Active</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
