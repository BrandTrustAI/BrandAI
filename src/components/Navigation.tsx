import { NavLink } from "react-router-dom";
import { Sparkles, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";

const Navigation = () => {
  return (
    <nav className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <NavLink to="/" className="flex items-center gap-2 font-bold text-xl gradient-text">
            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            BrandAI
          </NavLink>
          
          <div className="flex gap-2">
            <NavLink
              to="/"
              className={({ isActive }) => cn(
                "px-4 py-2 rounded-lg font-medium transition-smooth flex items-center gap-2",
                isActive 
                  ? "bg-primary text-primary-foreground" 
                  : "hover:bg-secondary text-foreground"
              )}
            >
              <Sparkles className="w-4 h-4" />
              Generator
            </NavLink>
            <NavLink
              to="/critique"
              className={({ isActive }) => cn(
                "px-4 py-2 rounded-lg font-medium transition-smooth flex items-center gap-2",
                isActive 
                  ? "bg-primary text-primary-foreground" 
                  : "hover:bg-secondary text-foreground"
              )}
            >
              <BarChart3 className="w-4 h-4" />
              Critique
            </NavLink>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
