'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { getPterodactylContext } from '@/lib/pterodactyl-context';

// Define the shape of the context data
interface PterodactylContextValue {
  userId: string;
  username: string;
  serverId: string;
  serverName: string;
  apiToken?: string;
}

const PterodactylContext = createContext<PterodactylContextValue | null>(null);

export function PterodactylContextProvider({ children }: { children: React.ReactNode }) {
  const [context, setContext] = useState<PterodactylContextValue | null>(null);
  
  useEffect(() => {
    // Try to get context from URL
    let ctx = getPterodactylContext();
    
    // If not in URL, try to get from localStorage
    if (!ctx) {
      const storedContext = localStorage.getItem('pterodactyl_context');
      if (storedContext) {
        try {
          ctx = JSON.parse(storedContext);
        } catch (e) {
          console.error("Failed to parse stored Pterodactyl context:", e);
        }
      }
    }

    setContext(ctx);
    
    // Store in localStorage for persistence if context is found
    if (ctx) {
      localStorage.setItem('pterodactyl_context', JSON.stringify(ctx));
    }
  }, []);
  
  return (
    <PterodactylContext.Provider value={context}>
      {children}
    </PterodactylContext.Provider>
  );
}

export function usePterodactylContext() {
  return useContext(PterodactylContext);
}
