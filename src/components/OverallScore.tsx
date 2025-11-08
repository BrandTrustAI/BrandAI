import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface OverallScoreProps {
  score: number;
}

const OverallScore = ({ score }: OverallScoreProps) => {
  const getScoreColor = () => {
    if (score >= 70) return "text-success";
    if (score >= 40) return "text-warning";
    return "text-destructive";
  };

  const getCircleColor = () => {
    if (score >= 70) return "stroke-success";
    if (score >= 40) return "stroke-warning";
    return "stroke-destructive";
  };

  const getGradient = () => {
    if (score >= 70) return "from-success/10 to-success/5";
    if (score >= 40) return "from-warning/10 to-warning/5";
    return "from-destructive/10 to-destructive/5";
  };

  const circumference = 2 * Math.PI * 70;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <Card className={cn(
      "glass-card shadow-card p-8 text-center",
      "bg-gradient-to-br",
      getGradient()
    )}>
      <h2 className="text-lg font-semibold mb-6 text-card-foreground">Overall Score</h2>
      
      <div className="relative w-40 h-40 mx-auto mb-4">
        <svg className="transform -rotate-90 w-40 h-40">
          <circle
            cx="80"
            cy="80"
            r="70"
            stroke="currentColor"
            strokeWidth="8"
            fill="transparent"
            className="text-secondary"
          />
          <circle
            cx="80"
            cy="80"
            r="70"
            stroke="currentColor"
            strokeWidth="8"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className={cn("transition-all duration-1000", getCircleColor())}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={cn("text-5xl font-bold", getScoreColor())}>
            {score}
          </span>
        </div>
      </div>
      
      <p className="text-sm text-muted-foreground">
        {score >= 70 && "Excellent performance"}
        {score >= 40 && score < 70 && "Good with room for improvement"}
        {score < 40 && "Needs significant improvement"}
      </p>
    </Card>
  );
};

export default OverallScore;
