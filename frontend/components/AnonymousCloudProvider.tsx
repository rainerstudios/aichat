"use client";

import { AssistantRuntimeProvider, useLocalRuntime } from "@assistant-ui/react";
import { useMemo } from "react";

export function AnonymousCloudProvider({ children }: { children: React.ReactNode }) {
  const runtime = useLocalRuntime({
    adapter: {
      async run({ messages, system }) {
        const response = await fetch("/api/chat", {
          method: "POST", 
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages,
            system: system || "You are XGaming Server's AI support assistant.",
            tools: []
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        return {
          async *[Symbol.asyncIterator]() {
            const decoder = new TextDecoder();
            let buffer = "";

            try {
              while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                  if (line.trim()) {
                    // Parse backend streaming format
                    const match = line.match(/^0:"(.*)"/);
                    if (match) {
                      yield {
                        type: "text-delta" as const,
                        textDelta: match[1].replace(/\\"/g, '"'),
                      };
                    }
                  }
                }
              }
            } finally {
              reader.releaseLock();
            }
          },
        };
      },
    },
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}