"use client";

import { makeAssistantToolUI } from "@assistant-ui/react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Server as ServerIcon, 
  Cpu as CpuIcon, 
  MemoryStick as MemoryStickIcon, 
  HardDrive as HardDriveIcon, 
  Network as NetworkIcon,
  Play,
  Square,
  RefreshCw,
  AlertTriangle
} from "lucide-react";

type ServerStatusArgs = {
  server_id: string;
};

type ServerStatusResult = {
  server_name: string;
  status: "online" | "offline" | "starting" | "stopping";
  resources: {
    cpu_usage: number;
    memory_usage: number;
    memory_total: number;
    disk_usage: number;
    disk_total: number;
    network_rx: number;
    network_tx: number;
  };
  game_info: {
    players_online: number;
    max_players: number;
    game_version: string;
    uptime: string;
  };
  last_updated: string;
};

export const ServerStatusTool = makeAssistantToolUI<ServerStatusArgs, string>({
  toolName: "get_server_status",
  render: function ServerStatusUI({ args, result }) {
    let statusData: ServerStatusResult | { error: string } | null = null;
    
    try {
      statusData = result ? JSON.parse(result) : null;
    } catch {
      statusData = { error: result || "Failed to parse server status" };
    }

    const getStatusColor = (status: string) => {
      switch (status) {
        case "online": return "bg-green-500";
        case "offline": return "bg-red-500";
        case "starting": return "bg-yellow-500";
        case "stopping": return "bg-orange-500";
        default: return "bg-gray-500";
      }
    };

    const getStatusIcon = (status: string) => {
      switch (status) {
        case "online": return <Play className="h-4 w-4" />;
        case "offline": return <Square className="h-4 w-4" />;
        case "starting": case "stopping": return <RefreshCw className="h-4 w-4 animate-spin" />;
        default: return <AlertTriangle className="h-4 w-4" />;
      }
    };

    const formatBytes = (bytes: number) => {
      return (bytes / (1024 ** 3)).toFixed(1) + " GB";
    };

    const formatNetworkSpeed = (bytes: number) => {
      return (bytes / (1024 ** 2)).toFixed(1) + " MB/s";
    };

    return (
      <div className="mb-4 flex flex-col items-center gap-2">
        <pre className="whitespace-pre-wrap text-sm opacity-70">
          get_server_status({JSON.stringify(args)})
        </pre>
        
        {statusData && "error" in statusData && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 w-full max-w-lg">
            <p className="text-red-800 text-sm font-medium">❌ Error</p>
            <p className="text-red-700 text-sm">{statusData.error}</p>
          </div>
        )}

        {statusData && "server_name" in statusData && (
          <Card className="w-full max-w-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <ServerIcon className="h-6 w-6" />
                <div className="flex flex-col">
                  <span className="text-xl font-bold">{statusData.server_name}</span>
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(statusData.status)}`} />
                    <Badge variant={statusData.status === "online" ? "default" : "secondary"} className="flex items-center gap-1">
                      {getStatusIcon(statusData.status)}
                      {statusData.status.toUpperCase()}
                    </Badge>
                  </div>
                </div>
              </CardTitle>
            </CardHeader>
            
            <CardContent className="space-y-6">
              {/* Game Information */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-blue-600 text-sm font-medium mb-1">Players Online</p>
                  <p className="text-2xl font-bold text-blue-900">
                    {statusData.game_info.players_online}/{statusData.game_info.max_players}
                  </p>
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                  <p className="text-purple-600 text-sm font-medium mb-1">Uptime</p>
                  <p className="text-lg font-semibold text-purple-900">
                    {statusData.game_info.uptime}
                  </p>
                </div>
              </div>

              {/* Resource Usage */}
              <div className="space-y-3">
                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                  <CpuIcon className="h-4 w-4" />
                  Resource Usage
                </h3>
                
                {/* CPU Usage */}
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">CPU</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${statusData.resources.cpu_usage > 80 ? 'bg-red-500' : statusData.resources.cpu_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'}`}
                        style={{ width: `${statusData.resources.cpu_usage}%` }}
                      />
                    </div>
                    <span className="text-sm font-mono">{statusData.resources.cpu_usage}%</span>
                  </div>
                </div>

                {/* Memory Usage */}
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium flex items-center gap-1">
                    <MemoryStickIcon className="h-3 w-3" />
                    Memory
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${(statusData.resources.memory_usage / statusData.resources.memory_total) * 100 > 80 ? 'bg-red-500' : 'bg-blue-500'}`}
                        style={{ width: `${(statusData.resources.memory_usage / statusData.resources.memory_total) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-mono">
                      {formatBytes(statusData.resources.memory_usage)}/{formatBytes(statusData.resources.memory_total)}
                    </span>
                  </div>
                </div>

                {/* Disk Usage */}
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium flex items-center gap-1">
                    <HardDriveIcon className="h-3 w-3" />
                    Disk
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${(statusData.resources.disk_usage / statusData.resources.disk_total) * 100 > 90 ? 'bg-red-500' : 'bg-green-500'}`}
                        style={{ width: `${(statusData.resources.disk_usage / statusData.resources.disk_total) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-mono">
                      {formatBytes(statusData.resources.disk_usage)}/{formatBytes(statusData.resources.disk_total)}
                    </span>
                  </div>
                </div>

                {/* Network */}
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium flex items-center gap-1">
                    <NetworkIcon className="h-3 w-3" />
                    Network
                  </span>
                  <div className="text-sm font-mono">
                    ↓ {formatNetworkSpeed(statusData.resources.network_rx)} | ↑ {formatNetworkSpeed(statusData.resources.network_tx)}
                  </div>
                </div>
              </div>

              {/* Game Version & Last Updated */}
              <div className="pt-2 border-t border-gray-200 text-xs text-gray-500 flex justify-between">
                <span>Version: {statusData.game_info.game_version}</span>
                <span>Updated: {new Date(statusData.last_updated).toLocaleTimeString()}</span>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  },
});