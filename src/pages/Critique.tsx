import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Download, Upload, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import MediaViewer from "@/components/MediaViewer";
import ScoreCard from "@/components/ScoreCard";
import OverallScore from "@/components/OverallScore";
import FileUploadZone from "@/components/FileUploadZone";

interface CritiqueData {
  brandAlignment: number;
  visualQuality: number;
  messageClarity: number;
  safetyEthics: number;
  detailedFeedback: string[];
  suggestions: string[];
  jsonOutput: any;
}

const Critique = () => {
  const location = useLocation();
  const [mediaUrl, setMediaUrl] = useState<string | null>(location.state?.mediaUrl || null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [critiqueData, setCritiqueData] = useState<CritiqueData | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const mockCritiqueData: CritiqueData = {
    brandAlignment: 87,
    visualQuality: 92,
    messageClarity: 78,
    safetyEthics: 95,
    detailedFeedback: [
      "Strong brand color consistency throughout the visual elements",
      "Clear product positioning with good lighting and composition",
      "Message could be more concise for better audience retention",
      "Excellent adherence to brand guidelines and safety standards",
      "Consider adding subtle motion to increase engagement"
    ],
    suggestions: [
      "Simplify the tagline to 5-7 words for better memorability",
      "Add a subtle gradient overlay to enhance visual depth",
      "Consider A/B testing with a more direct call-to-action",
      "Increase contrast on text overlays for better readability"
    ],
    jsonOutput: {
      brand_alignment_score: 87,
      visual_quality_score: 92,
      message_clarity_score: 78,
      safety_score: 95,
      overall_score: 88,
      detailed_feedback: {
        strengths: [
          "Strong brand consistency",
          "High visual quality",
          "Safe content"
        ],
        weaknesses: [
          "Message clarity needs improvement"
        ]
      },
      violations: [],
      improvement_suggestions: [
        "Simplify messaging",
        "Enhance text readability"
      ]
    }
  };

  useEffect(() => {
    if (mediaUrl && !critiqueData) {
      analyzeContent();
    }
  }, [mediaUrl]);

  const analyzeContent = () => {
    setIsAnalyzing(true);
    // Simulate analysis
    setTimeout(() => {
      setCritiqueData(mockCritiqueData);
      setIsAnalyzing(false);
      toast.success("Analysis complete!");
    }, 2500);
  };

  const handleFileUpload = (file: File) => {
    setUploadedFile(file);
    const url = URL.createObjectURL(file);
    setMediaUrl(url);
    setCritiqueData(null);
  };

  const handleAnalyze = () => {
    if (mediaUrl) {
      analyzeContent();
    }
  };

  const handleDownloadReport = () => {
    toast.success("Report downloaded!");
  };

  const overallScore = critiqueData 
    ? Math.round((critiqueData.brandAlignment + critiqueData.visualQuality + critiqueData.messageClarity + critiqueData.safetyEthics) / 4)
    : 0;

  if (!mediaUrl) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-secondary/20 to-background flex items-center justify-center">
        <div className="container mx-auto px-4 py-8 max-w-2xl">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-3 gradient-text">Upload for Analysis</h1>
            <p className="text-muted-foreground text-lg">Upload your ad content to get AI-powered feedback</p>
          </div>
          
          <Card className="p-8 glass-card shadow-card">
            <FileUploadZone
              onFileSelect={handleFileUpload}
              accept="image/*,video/*"
              icon={<Upload className="w-12 h-12" />}
              large
            />
            
            {uploadedFile && (
              <Button 
                onClick={handleAnalyze}
                className="w-full mt-6 gradient-primary text-white font-semibold py-6 text-lg"
              >
                Analyze Content
              </Button>
            )}
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-secondary/20 to-background">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-3 gradient-text">Ad Critique Dashboard</h1>
          <p className="text-muted-foreground text-lg">AI-powered brand content analysis</p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left - Media Viewer */}
          <div>
            <MediaViewer url={mediaUrl} isAnalyzing={isAnalyzing} />
          </div>

          {/* Right - Critique Results */}
          <div className="space-y-6">
            {isAnalyzing ? (
              <Card className="p-12 glass-card shadow-card text-center">
                <div className="w-16 h-16 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4" />
                <p className="text-lg font-medium text-muted-foreground">Analyzing content...</p>
              </Card>
            ) : critiqueData ? (
              <>
                <OverallScore score={overallScore} />

                <div className="grid grid-cols-2 gap-4">
                  <ScoreCard
                    title="Brand Alignment"
                    score={critiqueData.brandAlignment}
                    icon="shield-check"
                  />
                  <ScoreCard
                    title="Visual Quality"
                    score={critiqueData.visualQuality}
                    icon="eye"
                  />
                  <ScoreCard
                    title="Message Clarity"
                    score={critiqueData.messageClarity}
                    icon="message-square"
                  />
                  <ScoreCard
                    title="Safety & Ethics"
                    score={critiqueData.safetyEthics}
                    icon="shield"
                  />
                </div>

                <Card className="glass-card shadow-card">
                  <Tabs defaultValue="feedback" className="w-full">
                    <TabsList className="w-full grid grid-cols-3">
                      <TabsTrigger value="feedback">Feedback</TabsTrigger>
                      <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
                      <TabsTrigger value="json">JSON</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="feedback" className="p-6">
                      <ul className="space-y-3">
                        {critiqueData.detailedFeedback.map((item, index) => (
                          <li key={index} className="flex gap-3 items-start">
                            <span className="w-1.5 h-1.5 rounded-full bg-primary mt-2 flex-shrink-0" />
                            <span className="text-sm text-card-foreground">{item}</span>
                          </li>
                        ))}
                      </ul>
                    </TabsContent>
                    
                    <TabsContent value="suggestions" className="p-6">
                      <ul className="space-y-3">
                        {critiqueData.suggestions.map((item, index) => (
                          <li key={index} className="flex gap-3 items-start">
                            <span className="text-accent font-bold flex-shrink-0">{index + 1}.</span>
                            <span className="text-sm text-card-foreground">{item}</span>
                          </li>
                        ))}
                      </ul>
                    </TabsContent>
                    
                    <TabsContent value="json" className="p-6">
                      <div className="relative">
                        <pre className="bg-secondary/50 rounded-lg p-4 overflow-x-auto text-xs">
                          <code>{JSON.stringify(critiqueData.jsonOutput, null, 2)}</code>
                        </pre>
                        <Button 
                          size="sm" 
                          variant="secondary"
                          className="absolute top-2 right-2"
                          onClick={() => {
                            navigator.clipboard.writeText(JSON.stringify(critiqueData.jsonOutput, null, 2));
                            toast.success("Copied to clipboard!");
                          }}
                        >
                          Copy
                        </Button>
                      </div>
                    </TabsContent>
                  </Tabs>
                </Card>

                <div className="flex gap-3">
                  <Button 
                    variant="outline" 
                    className="flex-1"
                    onClick={handleDownloadReport}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download Report
                  </Button>
                  <Button 
                    variant="outline"
                    className="flex-1"
                    onClick={() => setMediaUrl(null)}
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Upload New
                  </Button>
                </div>
              </>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Critique;
