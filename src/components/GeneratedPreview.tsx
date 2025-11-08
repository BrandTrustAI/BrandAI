import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

interface GeneratedPreviewProps {
  content: string | null;
  isGenerating: boolean;
  onSendToCritique: () => void;
}

const GeneratedPreview = ({ content, isGenerating, onSendToCritique }: GeneratedPreviewProps) => {
  return (
    <Card className="glass-card shadow-card sticky top-8 overflow-hidden">
      <div className="p-6">
        <h2 className="text-xl font-semibold mb-4">Preview</h2>
        
        <div className="aspect-video bg-secondary/30 rounded-lg overflow-hidden mb-4 relative">
          {isGenerating ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4" />
                <p className="text-sm text-muted-foreground">Generating your ad...</p>
              </div>
            </div>
          ) : content ? (
            <img 
              src={content} 
              alt="Generated ad preview" 
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center px-6">
                <div className="w-16 h-16 rounded-full bg-secondary/50 flex items-center justify-center mx-auto mb-4">
                  <div className="w-8 h-8 rounded-full bg-muted" />
                </div>
                <p className="text-sm text-muted-foreground">
                  Your generated ad will appear here
                </p>
              </div>
            </div>
          )}
        </div>

        {content && !isGenerating && (
          <Button 
            onClick={onSendToCritique}
            className="w-full gradient-primary text-white font-semibold py-5"
          >
            Send to Critique
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        )}
      </div>
    </Card>
  );
};

export default GeneratedPreview;
