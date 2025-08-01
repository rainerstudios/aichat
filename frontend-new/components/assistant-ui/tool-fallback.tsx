import { ToolCallMessagePartComponent } from "@assistant-ui/react";
import { CheckIcon, ChevronDownIcon, ChevronUpIcon, PlayIcon, LoaderIcon, AlertTriangleIcon } from "lucide-react";
import { useState } from "react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";

export const ToolFallback: ToolCallMessagePartComponent = ({
  toolName,
  argsText,
  result,
  status,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(true);
  
  const getStatusIcon = () => {
    switch (status.type) {
      case "running":
        return <LoaderIcon className="size-4 animate-spin text-blue-500" />;
      case "complete":
        return <CheckIcon className="size-4 text-green-500" />;
      case "error":
        return <AlertTriangleIcon className="size-4 text-red-500" />;
      default:
        return <PlayIcon className="size-4 text-gray-500" />;
    }
  };

  const getStatusBadge = () => {
    switch (status.type) {
      case "running":
        return <Badge variant="secondary" className="text-blue-600 bg-blue-50">Running</Badge>;
      case "complete":
        return <Badge variant="default" className="text-green-600 bg-green-50">Complete</Badge>;
      case "error":
        return <Badge variant="destructive">Error</Badge>;
      default:
        return <Badge variant="outline">Pending</Badge>;
    }
  };

  const isError = status.type === "error";
  const hasResult = result !== undefined;

  return (
    <div className={`mb-4 flex w-full flex-col gap-3 rounded-lg border py-3 ${isError ? 'border-red-200 bg-red-50' : 'border-gray-200'}`}>
      <div className="flex items-center gap-3 px-4">
        {getStatusIcon()}
        <div className="flex-grow">
          <div className="flex items-center gap-2">
            <p className="font-medium">
              {toolName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </p>
            {getStatusBadge()}
          </div>
          {status.type === "running" && (
            <p className="text-sm text-gray-600 mt-1">Executing server action...</p>
          )}
        </div>
        <Button 
          variant="ghost" 
          size="sm"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="h-8 w-8 p-0"
        >
          {isCollapsed ? <ChevronDownIcon className="h-4 w-4" /> : <ChevronUpIcon className="h-4 w-4" />}
        </Button>
      </div>
      
      {!isCollapsed && (
        <div className="flex flex-col gap-3 border-t pt-3">
          {/* Tool Arguments */}
          <div className="px-4">
            <p className="text-sm font-medium text-gray-700 mb-2">Parameters:</p>
            <div className="bg-gray-100 rounded-md p-3">
              <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono">{argsText}</pre>
            </div>
          </div>
          
          {/* Tool Result */}
          {hasResult && (
            <div className="border-t border-dashed px-4 pt-3">
              <p className="text-sm font-medium text-gray-700 mb-2">
                {isError ? "Error Details:" : "Result:"}
              </p>
              <div className={`rounded-md p-3 ${isError ? 'bg-red-100 border border-red-200' : 'bg-green-50 border border-green-200'}`}>
                <pre className={`text-sm whitespace-pre-wrap font-mono ${isError ? 'text-red-800' : 'text-green-800'}`}>
                  {typeof result === "string" ? result : JSON.stringify(result, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
