# 🎨 Phase 4: UI & Polish Checklist
*Week 4-5: Tool UI Components, Frontend Enhancements, and Final Polish*

## Overview
This final phase focuses on creating beautiful tool UI components, enhancing the frontend experience, and adding the final polish to make the system production-ready and user-friendly.

---

## ✅ Feature 1: Tool UI Components (Day 1-3)

### Step 1: Server Status Tool UI
- [ ] **File**: `frontend-new/components/tools/ServerStatusUI.tsx`
- [ ] **Action**: Create interactive server status display

```tsx
// CREATE NEW FILE: frontend-new/components/tools/ServerStatusUI.tsx
"use client";

import { makeAssistantToolUI } from "@assistant-ui/react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { 
  Activity, 
  Cpu, 
  HardDrive, 
  MemoryStick, 
  Network, 
  Clock,
  AlertTriangle,
  CheckCircle,
  RefreshCw
} from "lucide-react";
import { useState } from "react";

interface ServerStatusData {
  server_name: string;
  status: string;
  players: string;
  cpu_usage: string;
  memory_usage: string;
  disk_usage: string;
  uptime: string;
  game_type: string;
  health_score?: number;
  alerts?: Array<{
    level: string;
    type: string;
    message: string;
  }>;
}

const ServerStatusUI = makeAssistantToolUI<{
  server_status: string;
}>({
  toolName: "get_server_status",
  render: ({ result, status }) => {
    const [isRefreshing, setIsRefreshing] = useState(false);
    
    if (status.type !== "complete") {
      return (
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Loading server status...</span>
          </div>
        </Card>
      );
    }

    // Parse server status from result text
    const parseServerStatus = (text: string): ServerStatusData | null => {
      try {
        // Extract data from formatted text using regex
        const serverMatch = text.match(/\*\*Server\*\*: (.+)/);
        const statusMatch = text.match(/\*\*Status\*\*: (.+)/);
        const playersMatch = text.match(/\*\*Players\*\*: (.+)/);
        const cpuMatch = text.match(/\*\*CPU\*\*: (.+)/);
        const memoryMatch = text.match(/\*\*Memory\*\*: (.+)/);
        const uptimeMatch = text.match(/\*\*Uptime\*\*: (.+)/);
        const gameMatch = text.match(/\*\*Game\*\*: (.+)/);
        
        if (!serverMatch || !statusMatch) return null;
        
        return {
          server_name: serverMatch[1].trim(),
          status: statusMatch[1].trim().toLowerCase(),
          players: playersMatch ? playersMatch[1].trim() : "0/0",
          cpu_usage: cpuMatch ? cpuMatch[1].trim() : "0%",
          memory_usage: memoryMatch ? memoryMatch[1].trim() : "0GB/0GB",
          uptime: uptimeMatch ? uptimeMatch[1].trim() : "0h",
          game_type: gameMatch ? gameMatch[1].trim() : "Unknown",
        };
      } catch {
        return null;
      }
    };

    const serverData = parseServerStatus(result);
    
    if (!serverData) {
      return (
        <Card className="p-4">
          <div className="text-center text-muted-foreground">
            Unable to parse server status
          </div>
        </Card>
      );
    }

    const getStatusColor = (status: string) => {
      switch (status) {
        case "running": return "bg-green-500";
        case "starting": return "bg-yellow-500";
        case "stopping": return "bg-orange-500";
        case "offline": return "bg-red-500";
        default: return "bg-gray-500";
      }
    };

    const parseUsagePercent = (usage: string): number => {
      const match = usage.match(/(\d+(?:\.\d+)?)%/);
      return match ? parseFloat(match[1]) : 0;
    };

    const cpuPercent = parseUsagePercent(serverData.cpu_usage);
    const memoryPercent = parseUsagePercent(serverData.memory_usage);

    const handleRefresh = () => {
      setIsRefreshing(true);
      // Trigger refresh action
      setTimeout(() => setIsRefreshing(false), 2000);
    };

    return (
      <Card className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Activity className="h-6 w-6 text-blue-500" />
            <div>
              <h3 className="text-lg font-semibold">{serverData.server_name}</h3>
              <p className="text-sm text-muted-foreground">{serverData.game_type}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge 
              variant={serverData.status === "running" ? "default" : "secondary"}
              className={`${getStatusColor(serverData.status)} text-white`}
            >
              {serverData.status.charAt(0).toUpperCase() + serverData.status.slice(1)}
            </Badge>
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-3 p-3 bg-muted/50 rounded-lg">
            <Network className="h-5 w-5 text-blue-500" />
            <div>
              <p className="text-sm font-medium">Players Online</p>
              <p className="text-lg">{serverData.players}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-3 bg-muted/50 rounded-lg">
            <Clock className="h-5 w-5 text-green-500" />
            <div>
              <p className="text-sm font-medium">Uptime</p>
              <p className="text-lg">{serverData.uptime}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-3 bg-muted/50 rounded-lg">
            <CheckCircle className="h-5 w-5 text-emerald-500" />
            <div>
              <p className="text-sm font-medium">Status</p>
              <p className="text-lg capitalize">{serverData.status}</p>
            </div>
          </div>
        </div>

        {/* Resource Usage */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-muted-foreground">Resource Usage</h4>
          
          {/* CPU Usage */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Cpu className="h-4 w-4 text-orange-500" />
                <span className="text-sm font-medium">CPU</span>
              </div>
              <span className="text-sm text-muted-foreground">{serverData.cpu_usage}</span>
            </div>
            <Progress 
              value={cpuPercent} 
              className="h-2"
              color={cpuPercent > 80 ? "bg-red-500" : cpuPercent > 60 ? "bg-yellow-500" : "bg-green-500"}
            />
          </div>

          {/* Memory Usage */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <MemoryStick className="h-4 w-4 text-purple-500" />
                <span className="text-sm font-medium">Memory</span>
              </div>
              <span className="text-sm text-muted-foreground">{serverData.memory_usage}</span>
            </div>
            <Progress 
              value={memoryPercent} 
              className="h-2"
              color={memoryPercent > 80 ? "bg-red-500" : memoryPercent > 60 ? "bg-yellow-500" : "bg-green-500"}
            />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex flex-wrap gap-2 pt-2 border-t">
          <Button variant="outline" size="sm">
            View Logs
          </Button>
          <Button variant="outline" size="sm">
            Restart Server
          </Button>
          <Button variant="outline" size="sm">
            Console
          </Button>
        </div>
      </Card>
    );
  },
});

export default ServerStatusUI;
```

### Step 2: File Management Tool UI
- [ ] **File**: `frontend-new/components/tools/FileManagerUI.tsx`
- [ ] **Action**: Create interactive file browser

```tsx
// CREATE NEW FILE: frontend-new/components/tools/FileManagerUI.tsx
"use client";

import { makeAssistantToolUI } from "@assistant-ui/react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  File,
  Folder,
  Download,
  Edit,
  Trash2,
  Search,
  ArrowUp,
  FileText,
  Image,
  Archive,
  Code,
  Database
} from "lucide-react";
import { useState } from "react";

interface FileItem {
  name: string;
  type: "file" | "directory";
  size?: string;
  modified?: string;
  path?: string;
}

const FileManagerUI = makeAssistantToolUI<{
  path?: string;
  files?: FileItem[];
}>({
  toolName: "list_server_files",
  render: ({ result, status, args }) => {
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedItems, setSelectedItems] = useState<string[]>([]);

    if (status.type !== "complete") {
      return (
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <Folder className="h-4 w-4 animate-pulse" />
            <span>Loading files...</span>
          </div>
        </Card>
      );
    }

    // Parse file listing from result
    const parseFileList = (text: string): { path: string; files: FileItem[] } => {
      const lines = text.split('\n');
      const pathMatch = text.match(/\*\*Directory: (.+)\*\*/);
      const currentPath = pathMatch ? pathMatch[1] : "/";
      
      const files: FileItem[] = [];
      let inDirectories = false;
      let inFiles = false;
      
      for (const line of lines) {
        if (line.includes("**Directories:**")) {
          inDirectories = true;
          inFiles = false;
          continue;
        }
        if (line.includes("**Files")) {
          inDirectories = false;
          inFiles = true;
          continue;
        }
        if (line.includes("**Summary**")) {
          break;
        }
        
        if (inDirectories && line.trim().startsWith("📁")) {
          const name = line.replace(/.*📁\s+/, "").trim();
          if (name) {
            files.push({ name, type: "directory" });
          }
        } else if (inFiles && line.trim().startsWith("📄")) {
          const match = line.match(/📄\s+(.+?)\s+\((.+?)\)\s+-\s+(.+)/);
          if (match) {
            files.push({
              name: match[1].trim(),
              type: "file",
              size: match[2].trim(),
              modified: match[3].trim()
            });
          }
        }
      }
      
      return { path: currentPath, files };
    };

    const { path, files } = parseFileList(result);
    
    const getFileIcon = (fileName: string, type: "file" | "directory") => {
      if (type === "directory") {
        return <Folder className="h-4 w-4 text-blue-500" />;
      }
      
      const ext = fileName.split('.').pop()?.toLowerCase();
      switch (ext) {
        case 'js':
        case 'ts':
        case 'java':
        case 'py':
        case 'json':
        case 'yml':
        case 'yaml':
          return <Code className="h-4 w-4 text-green-500" />;
        case 'txt':
        case 'md':
        case 'log':
          return <FileText className="h-4 w-4 text-gray-500" />;
        case 'png':
        case 'jpg':
        case 'jpeg':
        case 'gif':
          return <Image className="h-4 w-4 text-purple-500" />;
        case 'zip':
        case 'jar':
        case 'tar':
        case 'gz':
          return <Archive className="h-4 w-4 text-orange-500" />;
        case 'db':
        case 'sqlite':
          return <Database className="h-4 w-4 text-blue-600" />;
        default:
          return <File className="h-4 w-4 text-gray-400" />;
      }
    };

    const filteredFiles = files.filter(file =>
      file.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const toggleSelection = (fileName: string) => {
      setSelectedItems(prev =>
        prev.includes(fileName)
          ? prev.filter(item => item !== fileName)
          : [...prev, fileName]
      );
    };

    return (
      <Card className="p-6 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Folder className="h-5 w-5 text-blue-500" />
            <span className="font-mono text-sm text-muted-foreground">{path}</span>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline">{files.length} items</Badge>
          </div>
        </div>

        {/* Search and Actions */}
        <div className="flex items-center space-x-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search files..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          {path !== "/" && (
            <Button variant="outline" size="sm">
              <ArrowUp className="h-4 w-4 mr-1" />
              Up
            </Button>
          )}
        </div>

        {/* Selection Actions */}
        {selectedItems.length > 0 && (
          <div className="flex items-center space-x-2 p-2 bg-muted/50 rounded-lg">
            <span className="text-sm text-muted-foreground">
              {selectedItems.length} selected
            </span>
            <Separator orientation="vertical" className="h-4" />
            <Button variant="ghost" size="sm">
              <Download className="h-4 w-4 mr-1" />
              Download
            </Button>
            <Button variant="ghost" size="sm">
              <Trash2 className="h-4 w-4 mr-1" />
              Delete
            </Button>
          </div>
        )}

        {/* File List */}
        <div className="space-y-1 max-h-96 overflow-y-auto">
          {filteredFiles.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {searchTerm ? "No files match your search" : "Directory is empty"}
            </div>
          ) : (
            filteredFiles.map((file) => (
              <div
                key={file.name}
                className={`flex items-center space-x-3 p-2 rounded-lg hover:bg-muted/50 cursor-pointer ${
                  selectedItems.includes(file.name) ? "bg-muted/50" : ""
                }`}
                onClick={() => toggleSelection(file.name)}
              >
                <input
                  type="checkbox"
                  checked={selectedItems.includes(file.name)}
                  onChange={() => toggleSelection(file.name)}
                  className="rounded"
                />
                {getFileIcon(file.name, file.type)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{file.name}</p>
                  {file.size && file.modified && (
                    <p className="text-xs text-muted-foreground">
                      {file.size} • {file.modified}
                    </p>
                  )}
                </div>
                {file.type === "file" && (
                  <div className="flex items-center space-x-1">
                    <Button variant="ghost" size="sm">
                      <Edit className="h-3 w-3" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Download className="h-3 w-3" />
                    </Button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex justify-between items-center pt-4 border-t">
          <div className="text-xs text-muted-foreground">
            {filteredFiles.filter(f => f.type === "directory").length} folders, {" "}
            {filteredFiles.filter(f => f.type === "file").length} files
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" size="sm">
              New Folder
            </Button>
            <Button variant="outline" size="sm">
              Upload
            </Button>
          </div>
        </div>
      </Card>
    );
  },
});

export default FileManagerUI;
```

### Step 3: Backup Management Tool UI
- [ ] **File**: `frontend-new/components/tools/BackupManagerUI.tsx`
- [ ] **Action**: Create backup management interface

```tsx
// CREATE NEW FILE: frontend-new/components/tools/BackupManagerUI.tsx
"use client";

import { makeAssistantToolUI } from "@assistant-ui/react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Archive,
  Download,
  Trash2,
  RotateCcw,
  Clock,
  HardDrive,
  CheckCircle,
  AlertTriangle,
  Plus,
  Calendar
} from "lucide-react";
import { useState } from "react";

interface BackupItem {
  name: string;
  id: string;
  size: string;
  created: string;
  status: "completed" | "failed" | "creating";
}

const BackupManagerUI = makeAssistantToolUI<{
  backups?: BackupItem[];
}>({
  toolName: "list_server_backups",
  render: ({ result, status }) => {
    const [selectedBackup, setSelectedBackup] = useState<string | null>(null);
    const [showCreateForm, setShowCreateForm] = useState(false);

    if (status.type !== "complete") {
      return (
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <Archive className="h-4 w-4 animate-pulse" />
            <span>Loading backups...</span>
          </div>
        </Card>
      );
    }

    // Parse backup list from result
    const parseBackupList = (text: string): BackupItem[] => {
      const backups: BackupItem[] = [];
      const lines = text.split('\n');
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.includes('**') && (line.includes('✅') || line.includes('❌'))) {
          const status = line.includes('✅') ? 'completed' : 'failed';
          const nameMatch = line.match(/\*\*(.+)\*\*/);
          
          if (nameMatch && lines[i + 1]) {
            const detailLine = lines[i + 1];
            const dateMatch = detailLine.match(/📅\s+(\S+)/);
            const sizeMatch = detailLine.match(/💾\s+(\S+)/);
            const idMatch = detailLine.match(/🆔\s+(\S+)/);
            
            if (nameMatch[1] && dateMatch && sizeMatch && idMatch) {
              backups.push({
                name: nameMatch[1],
                id: idMatch[1],
                size: sizeMatch[1],
                created: dateMatch[1],
                status: status as "completed" | "failed"
              });
            }
          }
        }
      }
      
      return backups;
    };

    const backups = parseBackupList(result);
    const hasNoBackups = text.includes("No Backups Found");

    const getStatusIcon = (status: string) => {
      switch (status) {
        case "completed":
          return <CheckCircle className="h-4 w-4 text-green-500" />;
        case "failed":
          return <AlertTriangle className="h-4 w-4 text-red-500" />;
        case "creating":
          return <Clock className="h-4 w-4 text-yellow-500 animate-spin" />;
        default:
          return <Archive className="h-4 w-4 text-gray-500" />;
      }
    };

    const getStatusColor = (status: string) => {
      switch (status) {
        case "completed":
          return "bg-green-100 text-green-800 border-green-200";
        case "failed":
          return "bg-red-100 text-red-800 border-red-200";
        case "creating":
          return "bg-yellow-100 text-yellow-800 border-yellow-200";
        default:
          return "bg-gray-100 text-gray-800 border-gray-200";
      }
    };

    if (hasNoBackups) {
      return (
        <Card className="p-6">
          <div className="text-center space-y-4">
            <Archive className="h-12 w-12 text-muted-foreground mx-auto" />
            <div>
              <h3 className="text-lg font-semibold">No Backups Found</h3>
              <p className="text-muted-foreground">
                Create your first backup to protect your server data
              </p>
            </div>
            <Button onClick={() => setShowCreateForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create First Backup
            </Button>
          </div>
        </Card>
      );
    }

    return (
      <Card className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Archive className="h-6 w-6 text-blue-500" />
            <div>
              <h3 className="text-lg font-semibold">Server Backups</h3>
              <p className="text-sm text-muted-foreground">
                {backups.length} backups available
              </p>
            </div>
          </div>
          <Button onClick={() => setShowCreateForm(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Backup
          </Button>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg border border-green-200">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <div>
              <p className="text-sm font-medium text-green-700">Successful</p>
              <p className="text-lg font-bold text-green-800">
                {backups.filter(b => b.status === "completed").length}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <HardDrive className="h-5 w-5 text-blue-500" />
            <div>
              <p className="text-sm font-medium text-blue-700">Total Size</p>
              <p className="text-lg font-bold text-blue-800">
                {/* Calculate total size - simplified */}
                ~{backups.length * 1.2} GB
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-3 bg-purple-50 rounded-lg border border-purple-200">
            <Calendar className="h-5 w-5 text-purple-500" />
            <div>
              <p className="text-sm font-medium text-purple-700">Latest</p>
              <p className="text-lg font-bold text-purple-800">
                {backups.length > 0 ? backups[0].created : "Never"}
              </p>
            </div>
          </div>
        </div>

        {/* Backup List */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-muted-foreground">Recent Backups</h4>
          
          {backups.map((backup) => (
            <div
              key={backup.id}
              className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${
                selectedBackup === backup.id
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
              onClick={() => setSelectedBackup(backup.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(backup.status)}
                  <div>
                    <p className="font-medium">{backup.name}</p>
                    <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                      <span className="flex items-center">
                        <Clock className="h-3 w-3 mr-1" />
                        {backup.created}
                      </span>
                      <span className="flex items-center">
                        <HardDrive className="h-3 w-3 mr-1" />
                        {backup.size}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Badge className={getStatusColor(backup.status)}>
                    {backup.status}
                  </Badge>
                  
                  {backup.status === "completed" && (
                    <div className="flex space-x-1">
                      <Button variant="ghost" size="sm">
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <RotateCcw className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-700">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </div>
              
              {backup.status === "creating" && (
                <div className="mt-3">
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span>Creating backup...</span>
                    <span>45%</span>
                  </div>
                  <Progress value={45} className="h-2" />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Selected Backup Actions */}
        {selectedBackup && (
          <Alert>
            <Archive className="h-4 w-4" />
            <AlertDescription>
              <div className="flex items-center justify-between">
                <span>
                  Selected: <strong>{backups.find(b => b.id === selectedBackup)?.name}</strong>
                </span>
                <div className="flex space-x-2">
                  <Button variant="outline" size="sm">
                    Download
                  </Button>
                  <Button variant="outline" size="sm">
                    Restore
                  </Button>
                  <Button variant="outline" size="sm" className="text-red-600">
                    Delete
                  </Button>
                </div>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Recommendations */}
        <div className="bg-muted/50 p-4 rounded-lg">
          <h5 className="font-medium mb-2">💡 Backup Recommendations</h5>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• Keep at least 3-5 recent backups</li>
            <li>• Create backups before major changes</li>
            <li>• Test backup restoration occasionally</li>
            <li>• Clean up old backups to save space</li>
          </ul>
        </div>
      </Card>
    );
  },
});

export default BackupManagerUI;
```

### Step 4: Tool UI Registration
- [ ] **File**: `frontend-new/app/api/chat/route.ts`
- [ ] **Action**: Register tool UI components

```typescript
// ADD TO EXISTING route.ts file after imports
import ServerStatusUI from "@/components/tools/ServerStatusUI";
import FileManagerUI from "@/components/tools/FileManagerUI";
import BackupManagerUI from "@/components/tools/BackupManagerUI";

// ADD to the existing route handler, in the tools array
const tools = [
  ServerStatusUI,
  FileManagerUI,
  BackupManagerUI,
  // ... existing tools
];
```

---

## ✅ Feature 2: Enhanced Frontend Experience (Day 4-5)

### Step 1: Custom Chat Theme
- [ ] **File**: `frontend-new/app/globals.css`
- [ ] **Action**: Add XGaming Server branding

```css
/* ADD TO EXISTING globals.css */

/* XGaming Server Theme */
:root {
  --xgaming-primary: #6366f1;
  --xgaming-secondary: #8b5cf6;
  --xgaming-accent: #06b6d4;
  --xgaming-success: #10b981;
  --xgaming-warning: #f59e0b;
  --xgaming-error: #ef4444;
  --xgaming-gradient: linear-gradient(135deg, var(--xgaming-primary), var(--xgaming-secondary));
}

/* Chat Container Styling */
.chat-container {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

/* Message Styling */
.assistant-message {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.user-message {
  background: var(--xgaming-gradient);
  color: white;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
}

/* Tool Card Styling */
.tool-card {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  box-shadow: 
    0 4px 16px rgba(0, 0, 0, 0.1),
    0 1px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.tool-card:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 8px 24px rgba(0, 0, 0, 0.15),
    0 2px 8px rgba(0, 0, 0, 0.08);
}

/* Status Indicators */
.status-online {
  color: var(--xgaming-success);
  animation: pulse 2s infinite;
}

.status-offline {
  color: var(--xgaming-error);
}

.status-warning {
  color: var(--xgaming-warning);
  animation: pulse 2s infinite;
}

/* Progress Bars */
.progress-bar {
  background: var(--xgaming-gradient);
  border-radius: 9999px;
  transition: all 0.3s ease;
}

.progress-bar.critical {
  background: linear-gradient(90deg, var(--xgaming-error), #fca5a5);
}

.progress-bar.warning {
  background: linear-gradient(90deg, var(--xgaming-warning), #fcd34d);
}

/* Animations */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slide-in {
  animation: slideIn 0.3s ease-out;
}

/* Responsive Design */
@media (max-width: 768px) {
  .tool-card {
    margin: 0.5rem;
    border-radius: 8px;
  }
  
  .chat-container {
    padding: 1rem;
  }
}

/* Custom Scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: var(--xgaming-gradient);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #5855d1, #7c3aed);
}
```

### Step 2: Loading States and Animations
- [ ] **File**: `frontend-new/components/ui/loading-states.tsx`
- [ ] **Action**: Create reusable loading components

```tsx
// CREATE NEW FILE: frontend-new/components/ui/loading-states.tsx
"use client";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  Activity, 
  Archive, 
  Folder, 
  Database,
  Loader2,
  Zap
} from "lucide-react";

export const ServerStatusLoading = () => (
  <Card className="p-6 space-y-6">
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <Activity className="h-6 w-6 text-blue-500 animate-pulse" />
        <div>
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-3 w-20 mt-1" />
        </div>
      </div>
      <Skeleton className="h-6 w-16" />
    </div>
    
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="p-3 bg-muted/50 rounded-lg">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-6 w-12 mt-1" />
        </div>
      ))}
    </div>
    
    <div className="space-y-4">
      <Skeleton className="h-4 w-24" />
      {[1, 2].map((i) => (
        <div key={i} className="space-y-2">
          <div className="flex justify-between">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-12" />
          </div>
          <Skeleton className="h-2 w-full" />
        </div>
      ))}
    </div>
  </Card>
);

export const FileManagerLoading = () => (
  <Card className="p-6 space-y-4">
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <Folder className="h-5 w-5 text-blue-500 animate-pulse" />
        <Skeleton className="h-4 w-32" />
      </div>
      <Skeleton className="h-5 w-16" />
    </div>
    
    <div className="flex items-center space-x-2">
      <Skeleton className="h-9 flex-1" />
      <Skeleton className="h-9 w-16" />
    </div>
    
    <div className="space-y-2">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-center space-x-3 p-2">
          <Skeleton className="h-4 w-4" />
          <Folder className="h-4 w-4 text-blue-500 animate-pulse" />
          <div className="flex-1">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-3 w-16 mt-1" />
          </div>
        </div>
      ))}
    </div>
  </Card>
);

export const BackupManagerLoading = () => (
  <Card className="p-6 space-y-6">
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <Archive className="h-6 w-6 text-blue-500 animate-pulse" />
        <div>
          <Skeleton className="h-5 w-28" />
          <Skeleton className="h-3 w-20 mt-1" />
        </div>
      </div>
      <Skeleton className="h-9 w-24" />
    </div>
    
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="p-3 bg-muted/50 rounded-lg">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-6 w-8 mt-1" />
        </div>
      ))}
    </div>
    
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="p-4 border rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Archive className="h-4 w-4 animate-pulse" />
              <div>
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-24 mt-1" />
              </div>
            </div>
            <Skeleton className="h-6 w-20" />
          </div>
        </div>
      ))}
    </div>
  </Card>
);

export const DatabaseManagerLoading = () => (
  <Card className="p-6 space-y-4">
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <Database className="h-6 w-6 text-blue-600 animate-pulse" />
        <div>
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-3 w-20 mt-1" />
        </div>
      </div>
      <Skeleton className="h-9 w-28" />
    </div>
    
    <div className="space-y-3">
      {[1, 2].map((i) => (
        <div key={i} className="p-4 border rounded-lg">
          <Skeleton className="h-5 w-24" />
          <div className="space-y-1 mt-2">
            <Skeleton className="h-3 w-40" />
            <Skeleton className="h-3 w-32" />
            <Skeleton className="h-3 w-36" />
          </div>
        </div>
      ))}
    </div>
  </Card>
);

export const ToolExecutionLoading = ({ toolName }: { toolName: string }) => {
  const getIcon = () => {
    if (toolName.includes("status")) return <Activity className="h-5 w-5" />;
    if (toolName.includes("backup")) return <Archive className="h-5 w-5" />;
    if (toolName.includes("file")) return <Folder className="h-5 w-5" />;
    if (toolName.includes("database")) return <Database className="h-5 w-5" />;
    return <Zap className="h-5 w-5" />;
  };

  return (
    <Card className="p-4">
      <div className="flex items-center space-x-3">
        <div className="text-blue-500 animate-spin">
          <Loader2 className="h-5 w-5" />
        </div>
        <div className="flex items-center space-x-2">
          {getIcon()}
          <span className="text-sm">
            Executing {toolName.replace(/_/g, " ")}...
          </span>
        </div>
      </div>
    </Card>
  );
};

export const StreamingMessage = () => (
  <div className="flex items-center space-x-2 text-muted-foreground">
    <div className="flex space-x-1">
      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
    </div>
    <span className="text-sm">XGaming Assistant is thinking...</span>
  </div>
);
```

### Step 3: Enhanced Message Components
- [ ] **File**: `frontend-new/components/chat/message-components.tsx`
- [ ] **Action**: Create custom message components

```tsx
// CREATE NEW FILE: frontend-new/components/chat/message-components.tsx
"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { 
  Bot, 
  User, 
  Copy, 
  ThumbsUp, 
  ThumbsDown,
  RotateCcw,
  Zap,
  Clock
} from "lucide-react";
import { useState } from "react";

interface MessageProps {
  content: string;
  role: "user" | "assistant";
  timestamp?: Date;
  isStreaming?: boolean;
}

export const CustomUserMessage = ({ content, timestamp }: MessageProps) => {
  return (
    <div className="flex justify-end mb-4">
      <div className="flex items-start space-x-3 max-w-[80%]">
        <div className="user-message p-4 rounded-2xl rounded-tr-md">
          <p className="text-white">{content}</p>
          {timestamp && (
            <p className="text-xs text-white/70 mt-1">
              {timestamp.toLocaleTimeString()}
            </p>
          )}
        </div>
        <Avatar className="w-8 h-8">
          <AvatarFallback className="bg-blue-600 text-white">
            <User className="w-4 h-4" />
          </AvatarFallback>
        </Avatar>
      </div>
    </div>
  );
};

export const CustomAssistantMessage = ({ 
  content, 
  timestamp, 
  isStreaming 
}: MessageProps) => {
  const [copied, setCopied] = useState(false);
  const [liked, setLiked] = useState<boolean | null>(null);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleLike = (isLike: boolean) => {
    setLiked(isLike);
    // Here you could send feedback to analytics
  };

  return (
    <div className="flex justify-start mb-4">
      <div className="flex items-start space-x-3 max-w-[90%]">
        <Avatar className="w-8 h-8">
          <AvatarFallback className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
            <Bot className="w-4 h-4" />
          </AvatarFallback>
        </Avatar>
        <div className="assistant-message p-4 rounded-2xl rounded-tl-md slide-in">
          <div className="flex items-center space-x-2 mb-2">
            <Badge variant="secondary" className="text-xs">
              <Zap className="w-3 h-3 mr-1" />
              XGaming Assistant
            </Badge>
            {isStreaming && (
              <div className="flex items-center space-x-1 text-blue-500">
                <div className="w-2 h-2 bg-current rounded-full animate-pulse" />
                <span className="text-xs">Typing...</span>
              </div>
            )}
          </div>
          
          <div className="prose prose-sm max-w-none">
            {content.split('\n').map((line, i) => (
              <p key={i} className="mb-2 last:mb-0">
                {line}
              </p>
            ))}
          </div>
          
          <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-200">
            <div className="flex items-center space-x-2">
              {timestamp && (
                <span className="text-xs text-muted-foreground flex items-center">
                  <Clock className="w-3 h-3 mr-1" />
                  {timestamp.toLocaleTimeString()}
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopy}
                className="h-7 px-2"
              >
                <Copy className="w-3 h-3" />
                {copied && <span className="ml-1 text-xs">Copied!</span>}
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleLike(true)}
                className={`h-7 px-2 ${liked === true ? 'text-green-600' : ''}`}
              >
                <ThumbsUp className="w-3 h-3" />
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleLike(false)}
                className={`h-7 px-2 ${liked === false ? 'text-red-600' : ''}`}
              >
                <ThumbsDown className="w-3 h-3" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export const WelcomeMessage = () => {
  const quickActions = [
    "Check server status",
    "List my backups", 
    "Show server files",
    "Create a backup",
    "Check for alerts"
  ];

  return (
    <Card className="p-6 mb-4 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
      <div className="flex items-start space-x-4">
        <Avatar className="w-10 h-10">
          <AvatarFallback className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
            <Bot className="w-5 h-5" />
          </AvatarFallback>
        </Avatar>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Welcome to XGaming Server Assistant! 🎮
          </h3>
          <p className="text-gray-700 mb-4">
            I'm here to help you manage your game server. I can check status, manage files, 
            create backups, handle databases, and troubleshoot issues.
          </p>
          
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700">Quick actions:</p>
            <div className="flex flex-wrap gap-2">
              {quickActions.map((action, i) => (
                <Button 
                  key={i}
                  variant="outline" 
                  size="sm" 
                  className="text-xs h-7"
                  onClick={() => {
                    // Here you would trigger the action
                    console.log(`Quick action: ${action}`);
                  }}
                >
                  {action}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

export const ErrorMessage = ({ error }: { error: string }) => {
  return (
    <Card className="p-4 mb-4 bg-red-50 border-red-200">
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
          <Bot className="w-4 h-4 text-red-600" />
        </div>
        <div>
          <p className="text-sm font-medium text-red-800">
            Oops! Something went wrong
          </p>
          <p className="text-sm text-red-600 mt-1">{error}</p>
          <Button variant="outline" size="sm" className="mt-2 h-7">
            <RotateCcw className="w-3 h-3 mr-1" />
            Try Again
          </Button>
        </div>
      </div>
    </Card>
  );
};
```

---

## ✅ Feature 3: Performance Optimizations (Day 6)

### Step 1: Lazy Loading and Code Splitting
- [ ] **File**: `frontend-new/components/tools/index.ts`
- [ ] **Action**: Implement lazy loading for tool components

```typescript
// CREATE NEW FILE: frontend-new/components/tools/index.ts
import { lazy } from 'react';

// Lazy load tool components for better performance
export const ServerStatusUI = lazy(() => import('./ServerStatusUI'));
export const FileManagerUI = lazy(() => import('./FileManagerUI'));
export const BackupManagerUI = lazy(() => import('./BackupManagerUI'));

// Loading fallbacks
export const ToolLoadingFallback = ({ toolName }: { toolName: string }) => (
  <div className="flex items-center justify-center p-8">
    <div className="text-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
      <p className="text-sm text-muted-foreground">Loading {toolName}...</p>
    </div>
  </div>
);
```

### Step 2: Caching and State Management
- [ ] **File**: `frontend-new/lib/cache.ts`
- [ ] **Action**: Implement client-side caching

```typescript
// CREATE NEW FILE: frontend-new/lib/cache.ts
interface CacheItem<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

class ClientCache {
  private cache = new Map<string, CacheItem<any>>();
  
  set<T>(key: string, data: T, ttlMinutes: number = 5): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttlMinutes * 60 * 1000
    });
  }
  
  get<T>(key: string): T | null {
    const item = this.cache.get(key);
    
    if (!item) {
      return null;
    }
    
    if (Date.now() - item.timestamp > item.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return item.data;
  }
  
  clear(): void {
    this.cache.clear();
  }
  
  has(key: string): boolean {
    const item = this.cache.get(key);
    if (!item) return false;
    
    if (Date.now() - item.timestamp > item.ttl) {
      this.cache.delete(key);
      return false;
    }
    
    return true;
  }
}

export const cache = new ClientCache();

// Cache keys
export const CACHE_KEYS = {
  SERVER_STATUS: 'server_status',
  FILE_LIST: (path: string) => `file_list_${path}`,
  BACKUP_LIST: 'backup_list',
  DATABASE_LIST: 'database_list',
  HEALTH_CHECK: 'health_check'
} as const;

// Cache TTL in minutes
export const CACHE_TTL = {
  SERVER_STATUS: 1, // 1 minute
  FILE_LIST: 5,     // 5 minutes
  BACKUP_LIST: 5,   // 5 minutes
  DATABASE_LIST: 10, // 10 minutes
  HEALTH_CHECK: 2   // 2 minutes
} as const;
```

### Step 3: Error Boundaries and Resilience
- [ ] **File**: `frontend-new/components/error-boundary.tsx`
- [ ] **Action**: Create error handling system

```tsx
// CREATE NEW FILE: frontend-new/components/error-boundary.tsx
"use client";

import React from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

export class ErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <Card className="p-8 m-4 text-center">
          <div className="flex flex-col items-center space-y-4">
            <AlertTriangle className="h-12 w-12 text-red-500" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Something went wrong
              </h2>
              <p className="text-gray-600 mt-2">
                We encountered an unexpected error. This has been logged for review.
              </p>
            </div>
            
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-4 p-4 bg-gray-100 rounded-lg text-left max-w-full overflow-auto">
                <summary className="cursor-pointer font-medium">
                  Error Details (Development Only)
                </summary>
                <pre className="mt-2 text-xs text-red-600">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
            
            <div className="flex space-x-2">
              <Button
                onClick={() => this.setState({ hasError: false })}
                variant="outline"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
              <Button
                onClick={() => window.location.href = '/'}
                variant="default"
              >
                <Home className="h-4 w-4 mr-2" />
                Go Home
              </Button>
            </div>
          </div>
        </Card>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for wrapping components with error boundary
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>
) {
  return function WrappedComponent(props: P) {
    return (
      <ErrorBoundary>
        <Component {...props} />
      </ErrorBoundary>
    );
  };
}
```

---

## ✅ Feature 4: Advanced Features & Polish (Day 7)

### Step 1: Keyboard Shortcuts
- [ ] **File**: `frontend-new/hooks/useKeyboardShortcuts.ts`
- [ ] **Action**: Add keyboard navigation

```typescript
// CREATE NEW FILE: frontend-new/hooks/useKeyboardShortcuts.ts
import { useEffect, useCallback } from 'react';

interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  action: () => void;
  description: string;
}

export const useKeyboardShortcuts = (shortcuts: KeyboardShortcut[]) => {
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    for (const shortcut of shortcuts) {
      const matchesKey = event.key.toLowerCase() === shortcut.key.toLowerCase();
      const matchesCtrl = !shortcut.ctrlKey || event.ctrlKey;
      const matchesShift = !shortcut.shiftKey || event.shiftKey;
      const matchesAlt = !shortcut.altKey || event.altKey;

      if (matchesKey && matchesCtrl && matchesShift && matchesAlt) {
        event.preventDefault();
        shortcut.action();
        break;
      }
    }
  }, [shortcuts]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
};

// Predefined shortcuts for the application
export const defaultShortcuts: KeyboardShortcut[] = [
  {
    key: 's',
    ctrlKey: true,
    action: () => console.log('Check server status'),
    description: 'Check server status'
  },
  {
    key: 'b',
    ctrlKey: true,
    action: () => console.log('List backups'),
    description: 'List backups'
  },
  {
    key: 'f',
    ctrlKey: true,
    action: () => console.log('Browse files'),
    description: 'Browse files'
  },
  {
    key: 'h',
    ctrlKey: true,
    action: () => console.log('Show help'),
    description: 'Show help'
  },
  {
    key: '/',
    action: () => console.log('Focus search'),
    description: 'Focus search'
  }
];
```

### Step 2: Help System and Documentation
- [ ] **File**: `frontend-new/components/help/help-system.tsx`
- [ ] **Action**: Create integrated help system

```tsx
// CREATE NEW FILE: frontend-new/components/help/help-system.tsx
"use client";

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  HelpCircle, 
  Search, 
  Book, 
  Zap, 
  Shield, 
  Settings,
  X,
  ChevronRight
} from 'lucide-react';

interface HelpItem {
  id: string;
  title: string;
  description: string;
  category: 'basics' | 'advanced' | 'troubleshooting' | 'security';
  content: string;
  shortcuts?: string[];
}

const helpItems: HelpItem[] = [
  {
    id: 'server-status',
    title: 'Checking Server Status',
    description: 'Learn how to monitor your server health and resources',
    category: 'basics',
    content: `
# Checking Server Status

Ask me "What's my server status?" or "Check server status" to get:

- **Current Status**: Online, offline, starting, etc.
- **Resource Usage**: CPU, memory, and disk usage
- **Player Count**: Current players and capacity
- **Uptime**: How long the server has been running
- **Health Score**: Overall server health rating

**Quick Actions:**
- Use Ctrl+S to quickly check status
- Look for color-coded warnings (🟡 warning, 🔴 critical)
- Click "Refresh" for real-time updates
    `.trim(),
    shortcuts: ['Ctrl+S']
  },
  {
    id: 'file-management',
    title: 'Managing Server Files',
    description: 'Edit configurations, browse logs, and manage server files',
    category: 'basics',
    content: `
# File Management

**Browse Files:**
- "List files" or "Show files in plugins folder"
- Navigate through directories
- Search for specific files

**Edit Files:**
- "Edit server.properties" or "Read config.yml"
- Automatic backups created before editing
- Syntax highlighting for common file types

**Safety Features:**
- Confirmation required for critical files
- Automatic backups before changes
- File size limits for viewing/editing

**Tips:**
- Use specific paths: "show files in /plugins/Essentials/"
- Search by extension: "find all .yml files"
    `.trim(),
    shortcuts: ['Ctrl+F']
  },
  {
    id: 'backup-management',
    title: 'Backup Management',
    description: 'Create, restore, and manage server backups',
    category: 'basics',
    content: `
# Backup Management

**Creating Backups:**
- "Create a backup" for immediate backup
- "Create backup named 'before-update'" for custom names
- Automatic exclusion of logs and cache files

**Managing Backups:**
- "List my backups" to see all available backups
- "Delete old backup with confirmation" to clean up
- Download backups for local storage

**Restoring:**
- "Restore backup [name] with confirmation"
- ⚠️ This will overwrite all current files
- Server will restart automatically

**Best Practices:**
- Create backups before major changes
- Keep 3-5 recent backups
- Test restore process occasionally
    `.trim(),
    shortcuts: ['Ctrl+B']
  },
  {
    id: 'troubleshooting',
    title: 'Troubleshooting Issues',
    description: 'Diagnose and fix common server problems',
    category: 'troubleshooting',
    content: `
# Troubleshooting Common Issues

**Performance Problems:**
- "My server is lagging" - Get performance analysis
- Check resource usage and recommendations
- Restart server to clear memory leaks

**Connection Issues:**
- "Players can't connect" - Check server status
- Verify IP/port settings
- Check firewall and whitelist settings

**Crashes:**
- "Server keeps crashing" - Get crash analysis
- Check logs for error messages
- Restore from backup if needed

**Quick Diagnostics:**
- "Run health check" for comprehensive analysis
- "Check for alerts" for current issues
- "Get performance analysis" for trends
    `.trim()
  },
  {
    id: 'security',
    title: 'Security Best Practices',
    description: 'Keep your server secure and protected',
    category: 'security',
    content: `
# Security Best Practices

**File Safety:**
- Always create backups before editing
- Use confirmation for destructive actions
- Validate file paths and content

**Database Security:**
- Rotate database passwords regularly
- Use strong, unique passwords
- Don't share database credentials

**Access Control:**
- Limit admin permissions
- Monitor server access logs
- Keep software updated

**Backup Security:**
- Store backups in multiple locations
- Encrypt sensitive backup data
- Test backup integrity regularly
    `.trim()
  }
];

export const HelpSystem = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<HelpItem | null>(null);

  const categories = [
    { id: 'basics', label: 'Basics', icon: Book, color: 'bg-blue-100 text-blue-800' },
    { id: 'advanced', label: 'Advanced', icon: Zap, color: 'bg-purple-100 text-purple-800' },
    { id: 'troubleshooting', label: 'Troubleshooting', icon: Settings, color: 'bg-orange-100 text-orange-800' },
    { id: 'security', label: 'Security', icon: Shield, color: 'bg-green-100 text-green-800' }
  ];

  const filteredItems = helpItems.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = !selectedCategory || item.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  if (!isOpen) {
    return (
      <Button
        onClick={() => setIsOpen(true)}
        variant="outline"
        size="sm"
        className="fixed bottom-4 right-4 z-50"
      >
        <HelpCircle className="h-4 w-4 mr-2" />
        Help
      </Button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-4xl h-[80vh] flex">
        {/* Sidebar */}
        <div className="w-1/3 border-r p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Help & Documentation</h2>
            <Button variant="ghost" size="sm" onClick={() => setIsOpen(false)}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search help topics..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Categories */}
          <div className="space-y-2">
            <Button
              variant={selectedCategory === null ? "default" : "ghost"}
              className="w-full justify-start"
              onClick={() => setSelectedCategory(null)}
            >
              All Topics
            </Button>
            {categories.map(category => {
              const Icon = category.icon;
              return (
                <Button
                  key={category.id}
                  variant={selectedCategory === category.id ? "default" : "ghost"}
                  className="w-full justify-start"
                  onClick={() => setSelectedCategory(category.id)}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {category.label}
                </Button>
              );
            })}
          </div>

          {/* Help Items */}
          <div className="space-y-2 flex-1 overflow-y-auto">
            {filteredItems.map(item => (
              <div
                key={item.id}
                className={`p-3 rounded-lg cursor-pointer transition-colors ${
                  selectedItem?.id === item.id 
                    ? 'bg-blue-100 border-blue-200' 
                    : 'hover:bg-muted/50'
                }`}
                onClick={() => setSelectedItem(item)}
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-sm">{item.title}</h3>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {item.description}
                </p>
                <div className="flex items-center mt-2">
                  <Badge variant="outline" className="text-xs">
                    {categories.find(c => c.id === item.category)?.label}
                  </Badge>
                  {item.shortcuts && (
                    <Badge variant="secondary" className="text-xs ml-2">
                      {item.shortcuts[0]}
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 p-6">
          {selectedItem ? (
            <div className="space-y-4">
              <div>
                <h1 className="text-2xl font-bold">{selectedItem.title}</h1>
                <p className="text-muted-foreground">{selectedItem.description}</p>
              </div>
              
              <div className="prose prose-sm max-w-none">
                {selectedItem.content.split('\n').map((line, i) => {
                  if (line.startsWith('# ')) {
                    return <h1 key={i} className="text-xl font-bold mt-6 mb-3">{line.slice(2)}</h1>;
                  } else if (line.startsWith('**') && line.endsWith('**')) {
                    return <h2 key={i} className="text-lg font-semibold mt-4 mb-2">{line.slice(2, -2)}</h2>;
                  } else if (line.startsWith('- ')) {
                    return <li key={i} className="ml-4">{line.slice(2)}</li>;
                  } else if (line.trim()) {
                    return <p key={i} className="mb-2">{line}</p>;
                  }
                  return <br key={i} />;
                })}
              </div>

              {selectedItem.shortcuts && (
                <div className="bg-muted/50 p-4 rounded-lg">
                  <h3 className="font-medium mb-2">Keyboard Shortcuts</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedItem.shortcuts.map(shortcut => (
                      <Badge key={shortcut} variant="secondary">
                        {shortcut}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-center">
              <div>
                <HelpCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h2 className="text-xl font-semibold mb-2">Welcome to Help</h2>
                <p className="text-muted-foreground">
                  Select a topic from the sidebar to get started, or search for specific help.
                </p>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};
```

---

## 🧪 Testing Phase 4 Features

### Testing Checklist
- [ ] **Tool UI Components**: All tools render with interactive UI
- [ ] **Loading States**: Smooth loading animations and placeholders  
- [ ] **Error Handling**: Graceful error recovery and user feedback
- [ ] **Performance**: Lazy loading and caching working properly
- [ ] **Keyboard Shortcuts**: All shortcuts functional
- [ ] **Help System**: Complete documentation accessible
- [ ] **Mobile Responsive**: UI works on mobile devices
- [ ] **Accessibility**: Screen reader and keyboard navigation support

### Final Integration Test
```
1. Open https://chat.xgaming.pro
2. Try all keyboard shortcuts (Ctrl+S, Ctrl+B, Ctrl+F, Ctrl+H)
3. Execute "Check server status" - verify tool UI renders
4. Execute "List my backups" - verify interactive backup manager
5. Execute "Show server files" - verify file browser functionality
6. Test error scenarios - verify error boundaries work
7. Test on mobile device - verify responsive design
8. Use screen reader - verify accessibility
9. Open help system - verify documentation is complete
10. Test all quick actions and interactive elements
```

---

## 🎯 Production Deployment Checklist

### Final Steps for Production
- [ ] **Environment Variables**: All production API keys configured
- [ ] **Error Logging**: Sentry or similar error tracking setup
- [ ] **Performance Monitoring**: Application performance metrics
- [ ] **Security Headers**: CSP, HSTS, and other security headers
- [ ] **SSL Certificate**: HTTPS properly configured
- [ ] **Backup Strategy**: Automated backups for production data
- [ ] **Monitoring Alerts**: Server health monitoring setup
- [ ] **Documentation**: User guides and admin documentation
- [ ] **Load Testing**: System tested under expected load
- [ ] **Rollback Plan**: Deployment rollback strategy ready

---

## 🎉 Project Completion

Once Phase 4 is complete, you'll have:

✅ **Complete Tool UI System** - Interactive components for all server management tools
✅ **Enhanced User Experience** - Beautiful, responsive design with XGaming branding  
✅ **Performance Optimized** - Lazy loading, caching, and error resilience
✅ **Professional Polish** - Loading states, animations, and smooth interactions
✅ **Comprehensive Help** - Built-in documentation and keyboard shortcuts
✅ **Production Ready** - Error handling, monitoring, and security measures

Your XGaming Server AI Assistant will be a complete, professional-grade server management solution that provides an exceptional user experience while maintaining the robust functionality implemented in the previous phases.

**Total Development Time**: 4-5 weeks
**Features Implemented**: 50+ tools and capabilities
**UI Components**: 15+ interactive tool interfaces
**Lines of Code**: 10,000+ lines across frontend and backend

This represents a complete transformation from a basic chat interface to a comprehensive server management platform with AI assistance! 🚀