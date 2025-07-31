"use client";

import React from "react";
import { useAssistantRuntime } from "@assistant-ui/react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export function StreamingProgress({ className }: { className?: string }) {
  const { status } = useAssistantRuntime();

  if (status !== "in_progress") return null;

  return (
    <div className={cn("flex items-center gap-3 p-3 bg-muted/50 border rounded-lg", className)}>
      <div className="flex-shrink-0">
        <Loader2 className="h-4 w-4 animate-spin text-primary" />
      </div>
      
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground">
          Assistant is thinking...
        </p>
      </div>
    </div>
  );
}

export function StreamingStatusIndicator() {
  const { status } = useAssistantRuntime();

  if (status !== "in_progress") return null;
    
  return (
    <div className="flex items-center gap-1 text-primary">
      <Loader2 className="h-3 w-3 animate-spin" />
      <span className="text-xs">
        Processing...
      </span>
    </div>
  );
}
