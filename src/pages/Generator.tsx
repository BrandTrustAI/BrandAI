import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Card } from "@/components/ui/card";
import { Upload, Sparkles, ArrowRight, Image as ImageIcon } from "lucide-react";
import { toast } from "sonner";
import FileUploadZone from "@/components/FileUploadZone";
import GeneratedPreview from "@/components/GeneratedPreview";

const Generator = () => {
  const navigate = useNavigate();
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [productFile, setProductFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState("google-veo");
  const [duration, setDuration] = useState([10]);
  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedContent, setGeneratedContent] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!logoFile || !productFile || !prompt.trim()) {
      toast.error("Please upload both images and enter a prompt");
      return;
    }

    setIsGenerating(true);
    
    // Simulate generation process
    setTimeout(() => {
      // Mock generated image URL
      setGeneratedContent("https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800");
      setIsGenerating(false);
      toast.success("Ad generated successfully!");
    }, 3000);
  };

  const handleSendToCritique = () => {
    if (generatedContent) {
      navigate("/critique", { state: { mediaUrl: generatedContent } });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-secondary/20 to-background">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-3 gradient-text">AI Ad Generator</h1>
          <p className="text-muted-foreground text-lg">Create stunning brand advertisements with AI</p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Input Form */}
          <div className="space-y-6">
            <Card className="p-6 glass-card shadow-card transition-smooth hover:shadow-hover">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Upload className="w-5 h-5 text-primary" />
                Upload Assets
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Brand Logo</label>
                  <FileUploadZone
                    onFileSelect={setLogoFile}
                    accept="image/*"
                    icon={<ImageIcon className="w-8 h-8" />}
                  />
                  {logoFile && (
                    <p className="text-sm text-muted-foreground mt-2">
                      Selected: {logoFile.name}
                    </p>
                  )}
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Product Image</label>
                  <FileUploadZone
                    onFileSelect={setProductFile}
                    accept="image/*"
                    icon={<ImageIcon className="w-8 h-8" />}
                  />
                  {productFile && (
                    <p className="text-sm text-muted-foreground mt-2">
                      Selected: {productFile.name}
                    </p>
                  )}
                </div>
              </div>
            </Card>

            <Card className="p-6 glass-card shadow-card transition-smooth hover:shadow-hover">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-accent" />
                Generation Settings
              </h2>

              <div className="space-y-5">
                <div>
                  <label className="text-sm font-medium mb-2 block">Prompt</label>
                  <Textarea
                    placeholder="e.g., Create a 10-second energetic Nike ad featuring running shoes at sunrise"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    rows={4}
                    className="resize-none"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">AI Model</label>
                  <Select value={model} onValueChange={setModel}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="google-veo">Google Veo</SelectItem>
                      <SelectItem value="pika-labs">Pika Labs</SelectItem>
                      <SelectItem value="runway">Runway</SelectItem>
                      <SelectItem value="stable-diffusion">Stable Diffusion</SelectItem>
                      <SelectItem value="imagen-video">Imagen Video</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Duration: {duration[0]} seconds
                  </label>
                  <Slider
                    value={duration}
                    onValueChange={setDuration}
                    min={5}
                    max={15}
                    step={1}
                    className="py-4"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Aspect Ratio</label>
                  <Select value={aspectRatio} onValueChange={setAspectRatio}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="16:9">16:9 (Landscape)</SelectItem>
                      <SelectItem value="9:16">9:16 (Portrait)</SelectItem>
                      <SelectItem value="1:1">1:1 (Square)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button 
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full mt-6 gradient-primary text-white font-semibold py-6 text-lg"
              >
                {isGenerating ? (
                  <span className="flex items-center gap-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Generating...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5" />
                    Generate Ad
                  </span>
                )}
              </Button>
            </Card>
          </div>

          {/* Right Column - Preview */}
          <div>
            <GeneratedPreview 
              content={generatedContent}
              isGenerating={isGenerating}
              onSendToCritique={handleSendToCritique}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Generator;
