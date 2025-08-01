"use client";

import React, { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  Clock,
  Activity,
  Zap,
  Database,
  Network,
  Server
} from "lucide-react";

interface StreamingStep {
  id: string;
  label: string;
  status: "pending" | "running" | "complete" | "error";
  detail?: string;
  icon?: React.ReactNode;
}

interface StreamingProgressProps {
  steps: StreamingStep[];
  currentStep?: string;
  isRunning?: boolean;
  className?: string;
}

export const StreamingProgress: React.FC<StreamingProgressProps> = ({
  steps,
  currentStep,
  isRunning = false,
  className
}) => {
  const [animatedSteps, setAnimatedSteps] = useState<StreamingStep[]>(steps);

  useEffect(() => {
    setAnimatedSteps(steps);
  }, [steps]);

  const getStepIcon = (step: StreamingStep) => {
    if (step.icon) return step.icon;
    
    switch (step.status) {
      case "running":
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case "complete":
        return <CheckCircle2 className="h-4 w-4" />;
      case "error":
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const getStepColor = (step: StreamingStep) => {
    switch (step.status) {
      case "running":
        return "text-blue-500 bg-blue-50 border-blue-200";
      case "complete":
        return "text-green-500 bg-green-50 border-green-200";
      case "error":
        return "text-red-500 bg-red-50 border-red-200";
      default:
        return "text-gray-400 bg-gray-50 border-gray-200";
    }
  };

  return (
    <div className={cn("space-y-2", className)}>
      {animatedSteps.map((step, index) => (
        <div
          key={step.id}
          className={cn(
            "flex items-center gap-3 p-2 rounded-lg border transition-all duration-300",
            getStepColor(step),
            step.status === "running" && "shadow-sm animate-pulse"
          )}
        >
          <div className="flex-shrink-0">
            {getStepIcon(step)}
          </div>
          <div className="flex-grow min-w-0">
            <div className="text-sm font-medium truncate">{step.label}</div>
            {step.detail && (
              <div className="text-xs opacity-75 truncate">{step.detail}</div>
            )}
          </div>
          {step.status === "running" && (
            <div className="flex-shrink-0">
              <div className="h-1.5 w-16 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full animate-progress" />
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

// Animated status ticker for real-time updates
interface StatusTickerProps {
  messages: string[];
  speed?: number;
  className?: string;
}

export const StatusTicker: React.FC<StatusTickerProps> = ({
  messages,
  speed = 3000,
  className
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (messages.length <= 1) return;

    const interval = setInterval(() => {
      setIsAnimating(true);
      setTimeout(() => {
        setCurrentIndex((prev) => (prev + 1) % messages.length);
        setIsAnimating(false);
      }, 300);
    }, speed);

    return () => clearInterval(interval);
  }, [messages, speed]);

  if (messages.length === 0) return null;

  return (
    <div className={cn("relative overflow-hidden h-6", className)}>
      <div
        className={cn(
          "absolute inset-0 flex items-center px-2 text-sm text-gray-600 transition-all duration-300",
          isAnimating && "opacity-0 translate-y-2"
        )}
      >
        <Activity className="h-3 w-3 mr-2 text-blue-500" />
        {messages[currentIndex]}
      </div>
    </div>
  );
};

// Real-time metric display
interface MetricDisplayProps {
  label: string;
  value: string | number;
  unit?: string;
  icon?: React.ReactNode;
  trend?: "up" | "down" | "stable";
  className?: string;
}

export const MetricDisplay: React.FC<MetricDisplayProps> = ({
  label,
  value,
  unit,
  icon,
  trend,
  className
}) => {
  const getTrendIcon = () => {
    if (!trend) return null;
    
    switch (trend) {
      case "up":
        return <span className="text-green-500">↑</span>;
      case "down":
        return <span className="text-red-500">↓</span>;
      default:
        return <span className="text-gray-500">→</span>;
    }
  };

  return (
    <div className={cn("flex items-center gap-2 p-2 rounded-md bg-gray-50", className)}>
      {icon && <div className="text-gray-500">{icon}</div>}
      <div className="flex-grow">
        <div className="text-xs text-gray-500">{label}</div>
        <div className="flex items-baseline gap-1">
          <span className="text-lg font-semibold">{value}</span>
          {unit && <span className="text-sm text-gray-500">{unit}</span>}
          {getTrendIcon()}
        </div>
      </div>
    </div>
  );
};

// Add CSS for progress animation
const progressStyles = `
@keyframes progress {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.animate-progress {
  animation: progress 1.5s ease-in-out infinite;
}
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement("style");
  styleSheet.textContent = progressStyles;
  document.head.appendChild(styleSheet);
}