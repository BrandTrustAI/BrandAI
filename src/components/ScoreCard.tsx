import { Card } from "@/components/ui/card";
import { ShieldCheck, Eye, MessageSquare, Shield } from "lucide-react";
import { cn } from "@/lib/utils";

interface ScoreCardProps {
  title: string;
  score: number;
  icon: "shield-check" | "eye" | "message-square" | "shield";
}

const ScoreCard = ({ title, score, icon }: ScoreCardProps) => {
  const getIcon = () => {
    const iconClass = "w-5 h-5";
    switch (icon) {
      case "shield-check": return <ShieldCheck className={iconClass} />;
      case "eye": return <Eye className={iconClass} />;
      case "message-square": return <MessageSquare className={iconClass} />;
      case "shield": return <Shield className={iconClass} />;
    }
  };

  const getScoreColor = () => {
    if (score >= 70) return "text-success";
    if (score >= 40) return "text-warning";
    return "text-destructive";
  };

  const getGradientColor = () => {
    if (score >= 70) return "from-success/20 to-success/5";
    if (score >= 40) return "from-warning/20 to-warning/5";
    return "from-destructive/20 to-destructive/5";
  };

  return (
    <Card className={cn(
      "glass-card shadow-card transition-smooth hover:shadow-hover p-5",
      "bg-gradient-to-br",
      getGradientColor()
    )}>
      <div className="flex items-start justify-between mb-3">
        <div className="text-muted-foreground">
          {getIcon()}
        </div>
        <span className={cn("text-3xl font-bold", getScoreColor())}>
          {score}
        </span>
      </div>
      <h3 className="text-sm font-medium text-card-foreground">{title}</h3>
      
      {/* Progress bar */}
      <div className="mt-3 h-1.5 bg-secondary/50 rounded-full overflow-hidden">
        <div 
          className={cn(
            "h-full transition-all duration-1000 rounded-full",
            score >= 70 && "bg-success",
            score >= 40 && score < 70 && "bg-warning",
            score < 40 && "bg-destructive"
          )}
          style={{ width: `${score}%` }}
        />
      </div>
    </Card>
  );
};

export default ScoreCard;
