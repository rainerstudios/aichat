"use client";

import { makeAssistantToolUI } from "@assistant-ui/react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StreamingProgress, StatusTicker, MetricDisplay } from "@/components/ui/streaming-progress";
import { Database, Search, FileText, Brain, Zap, Clock } from "lucide-react";
import { useState, useEffect } from "react";

type AutoRAGQueryArgs = {
  query: string;
  knowledge_base?: string;
  max_results?: number;
};

type AutoRAGQueryResult = {
  results: Array<{
    id: string;
    title: string;
    content: string;
    score: number;
    source: string;
  }>;
  query_time: number;
  total_results: number;
  search_metadata: {
    embeddings_searched: number;
    collections_accessed: string[];
    query_expansion?: string[];
  };
};

export const AutoRAGQueryTool = makeAssistantToolUI<AutoRAGQueryArgs, string>({
  toolName: "query_autorag",
  render: function AutoRAGQueryUI({ args, result, status }) {
    const [steps, setSteps] = useState([
      { id: "init", label: "Initializing query", status: "pending" as const },
      { id: "embed", label: "Creating embeddings", status: "pending" as const },
      { id: "search", label: "Searching knowledge base", status: "pending" as const },
      { id: "rank", label: "Ranking results", status: "pending" as const },
      { id: "format", label: "Formatting response", status: "pending" as const }
    ]);

    const [statusMessages] = useState([
      "Connecting to AutoRAG service...",
      "Processing natural language query...",
      "Searching through knowledge vectors...",
      "Applying relevance scoring..."
    ]);

    // Simulate progress based on status
    useEffect(() => {
      if (status.type === "running") {
        let currentStep = 0;
        const interval = setInterval(() => {
          setSteps(prev => {
            const newSteps = [...prev];
            if (currentStep < newSteps.length) {
              // Complete previous step
              if (currentStep > 0) {
                newSteps[currentStep - 1].status = "complete";
              }
              // Start current step
              newSteps[currentStep].status = "running";
              currentStep++;
            }
            return newSteps;
          });
        }, 800);

        return () => clearInterval(interval);
      } else if (status.type === "complete" && result) {
        // Mark all steps as complete
        setSteps(prev => prev.map(step => ({ ...step, status: "complete" })));
      } else if (status.type === "incomplete") {
        // Mark current running step as error
        setSteps(prev => prev.map(step => 
          step.status === "running" ? { ...step, status: "error" } : step
        ));
      }
    }, [status.type, result]);

    let queryData: AutoRAGQueryResult | { error: string } | null = null;
    
    try {
      queryData = result ? JSON.parse(result) : null;
    } catch {
      queryData = { error: result || "Failed to parse query results" };
    }

    return (
      <div className="mb-4 w-full">
        <Card className="w-full">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <Database className="h-6 w-6 text-blue-500" />
              <div className="flex flex-col">
                <span className="text-xl font-bold">AutoRAG Knowledge Query</span>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant={status.type === "running" ? "secondary" : status.type === "complete" ? "default" : "destructive"}>
                    {status.type === "running" ? "Searching..." : status.type === "complete" ? "Complete" : "Error"}
                  </Badge>
                  <span className="text-sm text-gray-500">Query: &ldquo;{args.query}&rdquo;</span>
                </div>
              </div>
            </CardTitle>
          </CardHeader>
          
          <CardContent className="space-y-4">
            {/* Real-time status ticker */}
            {status.type === "running" && (
              <StatusTicker messages={statusMessages} speed={2000} />
            )}

            {/* Progress steps */}
            <StreamingProgress steps={steps} isRunning={status.type === "running"} />

            {/* Results section */}
            {queryData && "results" in queryData && (
              <div className="space-y-4 mt-6">
                {/* Query metrics */}
                <div className="grid grid-cols-3 gap-3">
                  <MetricDisplay
                    label="Query Time"
                    value={queryData.query_time.toFixed(2)}
                    unit="ms"
                    icon={<Clock className="h-4 w-4" />}
                  />
                  <MetricDisplay
                    label="Results Found"
                    value={queryData.total_results}
                    icon={<Search className="h-4 w-4" />}
                  />
                  <MetricDisplay
                    label="Embeddings Searched"
                    value={queryData.search_metadata.embeddings_searched}
                    icon={<Brain className="h-4 w-4" />}
                  />
                </div>

                {/* Search results */}
                <div className="space-y-3">
                  <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    Search Results
                  </h4>
                  
                  {queryData.results.map((item) => (
                    <div key={item.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-start justify-between mb-2">
                        <h5 className="font-medium text-gray-900">{item.title}</h5>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            {item.source}
                          </Badge>
                          <div className="flex items-center gap-1 text-sm text-gray-500">
                            <Zap className="h-3 w-3" />
                            {(item.score * 100).toFixed(1)}%
                          </div>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 line-clamp-3">{item.content}</p>
                    </div>
                  ))}
                </div>

                {/* Query expansion info */}
                {queryData.search_metadata.query_expansion && (
                  <div className="bg-blue-50 rounded-lg p-3">
                    <p className="text-sm text-blue-800">
                      <span className="font-medium">Query expanded with:</span> {queryData.search_metadata.query_expansion.join(", ")}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Error state */}
            {queryData && "error" in queryData && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-red-800 text-sm font-medium">❌ Query Error</p>
                <p className="text-red-700 text-sm mt-1">{queryData.error}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  },
});