"use client";

import React, { useState, useCallback, useMemo } from "react";
import { useExternalStoreRuntime, AssistantRuntimeProvider, ThreadMessageLike, AppendMessage } from "@assistant-ui/react";
import { Thread } from "@/components/assistant-ui/thread";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { Separator } from "@/components/ui/separator";
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb";
import { usePterodactylContext } from "@/components/PterodactylContextProvider";

// interface BackendThread {
//   thread_id: string;
//   title: string;
//   created_at: string;
//   updated_at?: string;
//   metadata?: Record<string, unknown>;
// }

interface ExternalStoreThreadData {
  threadId: string;
  title: string;
  status?: "regular" | "archived";
}

class ThreadErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode; fallback?: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Thread Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-lg mb-2">Something went wrong</div>
            <button 
              onClick={() => this.setState({ hasError: false })}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export const Assistant = () => {
  const pteroContext = usePterodactylContext();
  const [currentThreadId, setCurrentThreadId] = useState<string>("default");
  const [threads, setThreads] = useState<Map<string, ThreadMessageLike[]>>(new Map([["default", []]]));
  const [threadList, setThreadList] = useState<ExternalStoreThreadData[]>([{ threadId: "default", title: "New Chat", status: "regular" }]);
  const [isRunning, setIsRunning] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Get current messages for the active thread
  const currentMessages = threads.get(currentThreadId) || [];

  // No API loading needed - using local state only

  const generateResponse = useCallback(async (messages: ThreadMessageLike[]) => {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        messages: messages,
        pteroContext: pteroContext,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let assistantContent = "";

    if (reader) {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('0:"')) {
            try {
              const content = JSON.parse(line.slice(2));
              if (typeof content === 'string') {
                assistantContent += content;
              }
            } catch {
              // Skip invalid JSON
            }
          }
        }
      }
    }

    return assistantContent;
  }, [pteroContext]);

  const onNew = useCallback(async (message: AppendMessage) => {
    if (message.content[0]?.type !== "text") {
      throw new Error("Only text messages are supported");
    }

    const userMessage: ThreadMessageLike = {
      role: "user",
      content: message.content,
      id: `msg-${Date.now()}`,
      createdAt: new Date(),
    };

    // Add user message to current thread
    setThreads(prev => {
      const newMap = new Map(prev);
      const currentMessages = newMap.get(currentThreadId) || [];
      newMap.set(currentThreadId, [...currentMessages, userMessage]);
      return newMap;
    });

    setIsRunning(true);

    try {
      const assistantContent = await generateResponse([userMessage]);

      const assistantMessage: ThreadMessageLike = {
        role: "assistant",
        content: [{ type: "text", text: assistantContent }],
        id: `msg-${Date.now()}-assistant`,
        createdAt: new Date(),
      };

      // Add assistant message to current thread
      setThreads(prev => {
        const newMap = new Map(prev);
        const currentMessages = newMap.get(currentThreadId) || [];
        newMap.set(currentThreadId, [...currentMessages, assistantMessage]);
        return newMap;
      });

    } catch (error) {
      console.error('Chat API Error:', error);
    } finally {
      setIsRunning(false);
    }
  }, [currentThreadId, generateResponse]);

  const onReload = useCallback(async (parentId: string) => {
    const currentMessages = threads.get(currentThreadId) || [];
    
    // Find the parent message and get all messages up to that point
    const parentIndex = currentMessages.findIndex(msg => msg.id === parentId);
    if (parentIndex === -1) {
      console.warn('Parent message not found for reload');
      return;
    }

    // Get conversation history up to the parent message (excluding the assistant response we're reloading)
    const conversationHistory = currentMessages.slice(0, parentIndex + 1);
    
    // Remove the assistant message we're regenerating and any messages after it
    setThreads(prev => {
      const newMap = new Map(prev);
      newMap.set(currentThreadId, conversationHistory);
      return newMap;
    });

    setIsRunning(true);

    try {
      // Re-generate response using the conversation history
      const assistantContent = await generateResponse(conversationHistory);

      const newAssistantMessage: ThreadMessageLike = {
        role: "assistant",
        content: [{ type: "text", text: assistantContent }],
        id: `msg-${Date.now()}-assistant-reload`,
        createdAt: new Date(),
      };

      // Add the new assistant message
      setThreads(prev => {
        const newMap = new Map(prev);
        const currentMessages = newMap.get(currentThreadId) || [];
        newMap.set(currentThreadId, [...currentMessages, newAssistantMessage]);
        return newMap;
      });

    } catch (error) {
      console.error('Reload Error:', error);
    } finally {
      setIsRunning(false);
    }
  }, [currentThreadId, threads, generateResponse]);

  const threadListAdapter = useMemo(() => {
    // Ensure we have valid threads array
    const validThreads = threadList.filter(t => t.threadId && (t.status === "regular" || !t.status));
    const validArchivedThreads = threadList.filter(t => t.threadId && t.status === "archived");
    
    // Ensure we always have at least one thread
    const safeThreads = validThreads.length > 0 ? validThreads : [{ threadId: "default", title: "New Chat", status: "regular" as const }];
    
    return {
      threadId: currentThreadId,
      threads: safeThreads,
      archivedThreads: validArchivedThreads,

      onSwitchToNewThread: async () => {
        const newThreadId = `thread-${Date.now()}`;
        const newThreadData = {
          threadId: newThreadId,
          title: "New Chat",
          status: "regular" as const
        };
        
        setThreadList(prev => [newThreadData, ...prev]);
        setThreads(prev => new Map(prev).set(newThreadId, []));
        setCurrentThreadId(newThreadId);
      },

    onSwitchToThread: (threadId: string) => {
      setCurrentThreadId(threadId);
      // Initialize thread messages if not exists
      if (!threads.has(threadId)) {
        setThreads(prev => new Map(prev).set(threadId, []));
      }
    },

    onRename: async (threadId: string, newTitle: string) => {
      setThreadList(prev => 
        prev.map(t => 
          t.threadId === threadId ? { ...t, title: newTitle } : t
        )
      );
    },

    onArchive: async (threadId: string) => {
      setThreadList(prev => 
        prev.map(t => 
          t.threadId === threadId ? { ...t, status: "archived" as const } : t
        )
      );
      
      // Switch to another thread if this was the current one
      if (currentThreadId === threadId) {
        const remainingThreads = threadList.filter(t => t.threadId !== threadId && t.status === "regular");
        if (remainingThreads.length > 0) {
          setCurrentThreadId(remainingThreads[0].threadId);
        } else {
          // Create a new default thread
          const defaultThread = { threadId: "default", title: "New Chat", status: "regular" as const };
          setThreadList(prev => [...prev.filter(t => t.threadId !== threadId), defaultThread]);
          setCurrentThreadId("default");
          setThreads(prev => {
            const newMap = new Map(prev);
            newMap.delete(threadId);
            newMap.set("default", []);
            return newMap;
          });
        }
      }
    },

    onDelete: async (threadId: string) => {
      setThreadList(prev => prev.filter(t => t.threadId !== threadId));
      setThreads(prev => {
        const newMap = new Map(prev);
        newMap.delete(threadId);
        return newMap;
      });
      
      if (currentThreadId === threadId) {
        const remainingThreads = threadList.filter(t => t.threadId !== threadId);
        if (remainingThreads.length > 0) {
          setCurrentThreadId(remainingThreads[0].threadId);
        }
      }
    },
    };
  }, [currentThreadId, threadList, threads]);

  const convertMessage = (message: ThreadMessageLike) => {
    return message;
  };

  const runtime = useExternalStoreRuntime({
    messages: currentMessages,
    isRunning,
    onNew,
    onReload,
    setMessages: (messages) => {
      setThreads(prev => new Map(prev).set(currentThreadId, messages));
    },
    convertMessage,
    adapters: {
      threadList: threadListAdapter,
    },
  });

  // Runtime should be ready immediately now that we have convertMessage
  const runtimeReady = true;

  return (
    <div suppressHydrationWarning={true}>
      <AssistantRuntimeProvider runtime={runtime}>
        <SidebarProvider>
          {runtimeReady ? <AppSidebar /> : <div className="w-0" />}
          <SidebarInset>
            <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
              <SidebarTrigger />
              <Separator orientation="vertical" className="mr-2 h-4" />
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem className="hidden md:block">
                    <BreadcrumbLink href="#">XGaming Server</BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbPage>{pteroContext?.serverName || "AI Assistant"}</BreadcrumbPage>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </header>
            <div className="flex flex-1 overflow-hidden">
              <div className="flex-1">
                {isLoading || !runtimeReady ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <div className="text-lg">Loading threads...</div>
                    </div>
                  </div>
                ) : (
                  <ThreadErrorBoundary>
                    <Thread />
                  </ThreadErrorBoundary>
                )}
              </div>
            </div>
          </SidebarInset>
        </SidebarProvider>
      </AssistantRuntimeProvider>
    </div>
  );
};