"use client";

import { makeAssistantToolUI } from "@assistant-ui/react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StreamingProgress, StatusTicker, MetricDisplay } from "@/components/ui/streaming-progress";
import { 
  Server, 
  Play, 
  Square, 
  RefreshCw, 
  Terminal,
  Activity,
  Cpu,
  MemoryStick,
  Network
} from "lucide-react";
import { useState, useEffect } from "react";

type PterodactylActionArgs = {
  action: "start" | "stop" | "restart" | "kill" | "send_command";
  server_id: string;
  command?: string;
};

type PterodactylActionResult = {
  success: boolean;
  action: string;
  server_id: string;
  server_name: string;
  execution_time: number;
  server_state: {
    previous: string;
    current: string;
  };
  resource_usage?: {
    cpu: number;
    memory: number;
    disk: number;
  };
  logs?: string[];
};

export const PterodactylActionTool = makeAssistantToolUI<PterodactylActionArgs, string>({
  toolName: "pterodactyl_action",
  render: function PterodactylActionUI({ args, result, status }) {
    const [steps, setSteps] = useState(() => {
      const baseSteps = [
        { id: "auth", label: "Authenticating with panel", status: "pending" as const, icon: <Server className="h-4 w-4" /> },
        { id: "validate", label: "Validating server access", status: "pending" as const, icon: <Activity className="h-4 w-4" /> },
      ];

      // Add action-specific steps
      switch (args.action) {
        case "start":
          return [
            ...baseSteps,
            { id: "start", label: "Starting server", status: "pending" as const, icon: <Play className="h-4 w-4" /> },
            { id: "monitor", label: "Monitoring startup", status: "pending" as const, icon: <Activity className="h-4 w-4" /> },
            { id: "verify", label: "Verifying server status", status: "pending" as const, icon: <RefreshCw className="h-4 w-4" /> }
          ];
        case "stop":
          return [
            ...baseSteps,
            { id: "stop", label: "Stopping server gracefully", status: "pending" as const, icon: <Square className="h-4 w-4" /> },
            { id: "monitor", label: "Waiting for shutdown", status: "pending" as const, icon: <Activity className="h-4 w-4" /> },
            { id: "verify", label: "Verifying shutdown", status: "pending" as const, icon: <RefreshCw className="h-4 w-4" /> }
          ];
        case "restart":
          return [
            ...baseSteps,
            { id: "stop", label: "Stopping server", status: "pending" as const, icon: <Square className="h-4 w-4" /> },
            { id: "wait", label: "Waiting for shutdown", status: "pending" as const, icon: <RefreshCw className="h-4 w-4" /> },
            { id: "start", label: "Starting server", status: "pending" as const, icon: <Play className="h-4 w-4" /> },
            { id: "verify", label: "Verifying restart", status: "pending" as const, icon: <Activity className="h-4 w-4" /> }
          ];
        case "send_command":
          return [
            ...baseSteps,
            { id: "send", label: "Sending command", status: "pending" as const, icon: <Terminal className="h-4 w-4" /> },
            { id: "execute", label: "Executing on server", status: "pending" as const, icon: <Activity className="h-4 w-4" /> },
            { id: "capture", label: "Capturing output", status: "pending" as const, icon: <RefreshCw className="h-4 w-4" /> }
          ];
        default:
          return baseSteps;
      }
    });

    const [statusMessages] = useState(() => {
      const actionMessages = {
        start: [
          "Connecting to Pterodactyl API...",
          "Sending start signal to server...",
          "Waiting for server initialization...",
          "Server is starting up..."
        ],
        stop: [
          "Connecting to Pterodactyl API...",
          "Sending stop signal to server...",
          "Gracefully shutting down services...",
          "Server is shutting down..."
        ],
        restart: [
          "Connecting to Pterodactyl API...",
          "Initiating server restart...",
          "Waiting for clean shutdown...",
          "Starting server back up..."
        ],
        send_command: [
          "Connecting to server console...",
          "Preparing command execution...",
          "Sending command to server...",
          "Capturing command output..."
        ]
      };
      return actionMessages[args.action] || ["Processing action..."];
    });

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
                newSteps[currentStep - 1].detail = "Completed successfully";
              }
              // Start current step
              if (currentStep < newSteps.length) {
                newSteps[currentStep].status = "running";
                newSteps[currentStep].detail = "In progress...";
              }
              currentStep++;
            }
            return newSteps;
          });
        }, 1200);

        return () => clearInterval(interval);
      } else if (status.type === "complete" && result) {
        // Mark all steps as complete
        setSteps(prev => prev.map(step => ({ 
          ...step, 
          status: "complete",
          detail: "Completed successfully"
        })));
      } else if (status.type === "incomplete") {
        // Mark current running step as error
        setSteps(prev => prev.map(step => 
          step.status === "running" 
            ? { ...step, status: "error", detail: "Failed to complete" } 
            : step
        ));
      }
    }, [status.type, result]);

    let actionData: PterodactylActionResult | { error: string } | null = null;
    
    try {
      actionData = result ? JSON.parse(result) : null;
    } catch {
      actionData = { error: result || "Failed to parse action result" };
    }

    const getActionIcon = () => {
      switch (args.action) {
        case "start": return <Play className="h-6 w-6 text-green-500" />;
        case "stop": return <Square className="h-6 w-6 text-red-500" />;
        case "restart": return <RefreshCw className="h-6 w-6 text-blue-500" />;
        case "send_command": return <Terminal className="h-6 w-6 text-purple-500" />;
        default: return <Server className="h-6 w-6 text-gray-500" />;
      }
    };

    const getActionTitle = () => {
      switch (args.action) {
        case "start": return "Starting Server";
        case "stop": return "Stopping Server";
        case "restart": return "Restarting Server";
        case "send_command": return "Executing Command";
        default: return "Server Action";
      }
    };

    return (
      <div className="mb-4 w-full">
        <Card className="w-full">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              {getActionIcon()}
              <div className="flex flex-col">
                <span className="text-xl font-bold">{getActionTitle()}</span>
                <div className="flex items-center gap-2 mt-1">
                  <Badge 
                    variant={
                      status.type === "running" ? "secondary" : 
                      status.type === "complete" && actionData && "success" in actionData && actionData.success ? "default" : 
                      "destructive"
                    }
                  >
                    {status.type === "running" ? "Executing..." : 
                     status.type === "complete" && actionData && "success" in actionData && actionData.success ? "Success" : 
                     "Failed"}
                  </Badge>
                  <span className="text-sm text-gray-500">Server ID: {args.server_id}</span>
                  {args.command && (
                    <span className="text-sm text-gray-500">| Command: &ldquo;{args.command}&rdquo;</span>
                  )}
                </div>
              </div>
            </CardTitle>
          </CardHeader>
          
          <CardContent className="space-y-4">
            {/* Real-time status ticker */}
            {status.type === "running" && (
              <StatusTicker messages={statusMessages} speed={2500} />
            )}

            {/* Progress steps */}
            <StreamingProgress steps={steps} isRunning={status.type === "running"} />

            {/* Results section */}
            {actionData && "success" in actionData && (
              <div className="space-y-4 mt-6">
                {/* Action summary */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-gray-900">Action Summary</h4>
                    <Badge variant={actionData.success ? "default" : "destructive"}>
                      {actionData.success ? "Completed" : "Failed"}
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Server Name</p>
                      <p className="font-medium">{actionData.server_name}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Execution Time</p>
                      <p className="font-medium">{actionData.execution_time}ms</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Previous State</p>
                      <Badge variant="outline" className="mt-1">
                        {actionData.server_state.previous}
                      </Badge>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Current State</p>
                      <Badge 
                        variant={actionData.server_state.current === "running" ? "default" : "secondary"}
                        className="mt-1"
                      >
                        {actionData.server_state.current}
                      </Badge>
                    </div>
                  </div>
                </div>

                {/* Resource usage */}
                {actionData.resource_usage && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">Current Resource Usage</h4>
                    <div className="grid grid-cols-3 gap-3">
                      <MetricDisplay
                        label="CPU Usage"
                        value={actionData.resource_usage.cpu}
                        unit="%"
                        icon={<Cpu className="h-4 w-4" />}
                        trend={actionData.resource_usage.cpu > 80 ? "up" : "stable"}
                      />
                      <MetricDisplay
                        label="Memory"
                        value={actionData.resource_usage.memory}
                        unit="MB"
                        icon={<MemoryStick className="h-4 w-4" />}
                      />
                      <MetricDisplay
                        label="Disk"
                        value={actionData.resource_usage.disk}
                        unit="GB"
                        icon={<Network className="h-4 w-4" />}
                      />
                    </div>
                  </div>
                )}

                {/* Command logs */}
                {actionData.logs && actionData.logs.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Server Logs</h4>
                    <div className="bg-gray-900 text-gray-100 rounded-lg p-3 font-mono text-xs space-y-1 max-h-48 overflow-y-auto">
                      {actionData.logs.map((log, index) => (
                        <div key={index}>{log}</div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Error state */}
            {actionData && "error" in actionData && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-red-800 text-sm font-medium">❌ Action Error</p>
                <p className="text-red-700 text-sm mt-1">{actionData.error}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  },
});