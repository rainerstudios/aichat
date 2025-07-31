"use client";

import { makeAssistantToolUI } from "@assistant-ui/react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangleIcon, CheckIcon } from "lucide-react";

type RestartServerArgs = {
  server_id?: string;
};

export const RestartServerTool = makeAssistantToolUI<RestartServerArgs, string>({
  toolName: "restart_server",
  render: function RestartServerUI({ argsText, result, addResult }) {
    // Try to parse result as JSON for confirmation data
    let confirmationData = null;
    try {
      if (result && typeof result === "string") {
        const parsed = JSON.parse(result);
        if (parsed.requires_confirmation) {
          confirmationData = parsed;
        }
      }
    } catch {
      // If parsing fails, result is likely a success message
    }

    const handleConfirm = async () => {
      if (confirmationData) {
        // Call the tool again with confirmation data
        const confirmationResult = JSON.stringify({ 
          confirmed: true, 
          server_id: confirmationData.server_id 
        });
        addResult(confirmationResult);
      }
    };

    const handleCancel = async () => {
      addResult(JSON.stringify({ 
        confirmed: false, 
        cancelled: true 
      }));
    };

    return (
      <div className="mb-4 flex flex-col items-center gap-2">
        <pre className="whitespace-pre-wrap text-sm opacity-70">restart_server({argsText})</pre>
        
        {/* Show confirmation dialog if needed */}
        {confirmationData && (
          <Card className="mx-auto w-full max-w-md">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <AlertTriangleIcon className="text-orange-500" />
                Confirm Server Restart
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-2">
                <p className="text-muted-foreground text-sm font-medium">Server:</p>
                <p className="text-sm font-bold">{confirmationData.server_name}</p>
                <p className="text-muted-foreground text-sm font-medium">Status:</p>
                <p className="text-sm">{confirmationData.current_status}</p>
              </div>
              
              <div className="bg-orange-50 border border-orange-200 rounded-md p-3">
                <p className="text-orange-800 font-medium text-sm mb-2">⚠️ {confirmationData.warning}</p>
                <ul className="text-orange-700 text-sm space-y-1">
                  {confirmationData.impact.map((item: string, index: number) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end gap-2">
              <Button variant="outline" onClick={handleCancel}>
                Cancel
              </Button>
              <Button onClick={handleConfirm} className="bg-orange-600 hover:bg-orange-700">
                <CheckIcon className="mr-2 h-4 w-4" />
                Confirm Restart
              </Button>
            </CardFooter>
          </Card>
        )}

        {/* Show result if not a confirmation request */}
        {result && !confirmationData && (
          <div className="bg-green-50 border border-green-200 rounded-md p-4 w-full max-w-md">
            <pre className="whitespace-pre-wrap text-green-800 text-sm">{result}</pre>
          </div>
        )}
      </div>
    );
  },
});