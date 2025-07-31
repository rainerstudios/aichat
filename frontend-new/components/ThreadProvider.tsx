"use client";

import React, { createContext, useContext, useEffect, useState } from 'react';

interface Thread {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, unknown>;
}

interface ThreadContextType {
  threads: Thread[];
  currentThreadId: string | null;
  setCurrentThreadId: (id: string) => void;
  createNewThread: () => Promise<void>;
  archiveThread: (id: string) => Promise<void>;
  refreshThreads: () => Promise<void>;
}

const ThreadContext = createContext<ThreadContextType | null>(null);

export const useThreadContext = () => {
  const context = useContext(ThreadContext);
  if (!context) {
    throw new Error('useThreadContext must be used within a ThreadProvider');
  }
  return context;
};

export const ThreadProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);

  const refreshThreads = async () => {
    try {
      const response = await fetch('/api/threads');
      if (response.ok) {
        const threadData = await response.json();
        setThreads(threadData);
        
        // Set the first thread as current if none is selected
        if (!currentThreadId && threadData.length > 0) {
          setCurrentThreadId(threadData[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch threads:', error);
    }
  };

  const createNewThread = async () => {
    try {
      const response = await fetch('/api/threads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Chat' }),
      });
      
      if (response.ok) {
        const newThread = await response.json();
        setThreads(prev => [newThread, ...prev]);
        setCurrentThreadId(newThread.id);
      }
    } catch (error) {
      console.error('Failed to create thread:', error);
    }
  };

  const archiveThread = async (id: string) => {
    try {
      const response = await fetch(`/api/threads/${id}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        setThreads(prev => prev.filter(thread => thread.id !== id));
        
        // If we archived the current thread, switch to another one
        if (currentThreadId === id) {
          const remainingThreads = threads.filter(thread => thread.id !== id);
          setCurrentThreadId(remainingThreads.length > 0 ? remainingThreads[0].id : null);
        }
      }
    } catch (error) {
      console.error('Failed to archive thread:', error);
    }
  };

  useEffect(() => {
    refreshThreads();
  }, [refreshThreads]);

  const value: ThreadContextType = {
    threads,
    currentThreadId,
    setCurrentThreadId,
    createNewThread,
    archiveThread,
    refreshThreads,
  };

  return (
    <ThreadContext.Provider value={value}>
      {children}
    </ThreadContext.Provider>
  );
};