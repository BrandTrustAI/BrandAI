import { Card } from "@/components/ui/card";

interface MediaViewerProps {
  url: string;
  isAnalyzing?: boolean;
}

const MediaViewer = ({ url, isAnalyzing }: MediaViewerProps) => {
  const isVideo = url.includes('.mp4') || url.includes('.mov') || url.includes('video');

  return (
    <Card className="glass-card shadow-card sticky top-8 overflow-hidden">
      <div className="p-6">
        <h2 className="text-xl font-semibold mb-4">Media Content</h2>
        
        <div className="aspect-video bg-secondary/30 rounded-lg overflow-hidden relative">
          {isVideo ? (
            <video 
              src={url} 
              controls 
              className="w-full h-full object-cover"
            />
          ) : (
            <img 
              src={url} 
              alt="Ad content" 
              className="w-full h-full object-cover"
            />
          )}
          
          {isAnalyzing && (
            <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center">
              <div className="text-center">
                <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-3" />
                <p className="text-sm font-medium">Analyzing...</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

export default MediaViewer;
