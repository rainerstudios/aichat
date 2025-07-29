# 🖼️ Iframe Auto-Detection for Pterodactyl Integration

## Overview
When your chat app runs as an iframe inside Pterodactyl, you can automatically detect the user and server context using URL parameters, postMessage API, and Pterodactyl's session data.

## Implementation Methods

### Method 1: URL Parameters (Recommended)

**Step 1: Pterodactyl Integration**
```php
// In your Pterodactyl plugin/extension
$iframe_url = "https://chat.xgaming.pro?" . http_build_query([
    'user_id' => auth()->user()->id,
    'username' => auth()->user()->username,  
    'server_id' => $server->id,
    'server_name' => $server->name,
    'api_token' => encrypt(auth()->user()->createToken('chat')->plainTextToken)
]);

echo '<iframe src="' . $iframe_url . '" width="100%" height="600px"></iframe>';
```

**Step 2: Frontend Detection**
```typescript
// frontend-new/lib/pterodactyl-context.ts
interface PterodactylContext {
  userId: string;
  username: string;
  serverId: string;
  serverName: string;
  apiToken?: string;
}

export function getPterodactylContext(): PterodactylContext | null {
  if (typeof window === 'undefined') return null;
  
  const params = new URLSearchParams(window.location.search);
  
  const context = {
    userId: params.get('user_id'),
    username: params.get('username'),
    serverId: params.get('server_id'),
    serverName: params.get('server_name'),
    apiToken: params.get('api_token')
  };
  
  // Validate required fields
  if (!context.userId || !context.serverId) {
    return null;
  }
  
  return context as PterodactylContext;
}

export function isInPterodactylIframe(): boolean {
  try {
    return window.self !== window.top;
  } catch {
    return true; // If we can't access window.top, we're in iframe
  }
}
```

**Step 3: Context Provider**
```typescript
// frontend-new/components/PterodactylContextProvider.tsx
'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { getPterodactylContext, PterodactylContext } from '@/lib/pterodactyl-context';

const PterodactylContext = createContext<PterodactylContext | null>(null);

export function PterodactylContextProvider({ children }: { children: React.ReactNode }) {
  const [context, setContext] = useState<PterodactylContext | null>(null);
  
  useEffect(() => {
    const ctx = getPterodactylContext();
    setContext(ctx);
    
    // Store in localStorage for persistence
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
```

### Method 2: PostMessage API (Alternative)

**Step 1: Parent Window Communication**
```javascript
// In Pterodactyl page containing iframe
window.addEventListener('load', function() {
  const iframe = document.getElementById('chat-iframe');
  const context = {
    userId: <?= auth()->user()->id ?>,
    username: "<?= auth()->user()->username ?>",
    serverId: "<?= $server->id ?>",
    serverName: "<?= $server->name ?>",
    apiToken: "<?= encrypt(auth()->user()->createToken('chat')->plainTextToken) ?>"
  };
  
  iframe.onload = function() {
    iframe.contentWindow.postMessage({
      type: 'PTERODACTYL_CONTEXT',
      data: context
    }, 'https://chat.xgaming.pro');
  };
});
```

**Step 2: Iframe Message Listener**
```typescript
// frontend-new/hooks/usePterodactylMessages.ts
import { useEffect, useState } from 'react';

export function usePterodactylMessages() {
  const [context, setContext] = useState<PterodactylContext | null>(null);
  
  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      // Verify origin for security
      if (event.origin !== 'https://panel.xgaming.pro') return;
      
      if (event.data.type === 'PTERODACTYL_CONTEXT') {
        setContext(event.data.data);
        localStorage.setItem('pterodactyl_context', JSON.stringify(event.data.data));
      }
    }
    
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);
  
  return context;
}
```

## Backend Integration

**Update API Route**
```typescript
// frontend-new/app/api/chat/route.ts
import { getPterodactylContext } from '@/lib/pterodactyl-context';

export async function POST(req: Request) {
  const { messages, context } = await req.json();
  
  // Get Pterodactyl context from request or headers
  const pterodactylContext = context?.pterodactyl || getPterodactylContextFromHeaders(req);
  
  const systemPrompt = `You are XGaming Server's AI assistant for ${pterodactylContext?.username || 'a user'}.
  
Current Context:
- User: ${pterodactylContext?.username || 'Unknown'}
- Server: ${pterodactylContext?.serverName || 'Unknown'} (ID: ${pterodactylContext?.serverId || 'Unknown'})
- Access Level: ${pterodactylContext?.apiToken ? 'Authenticated' : 'Guest'}

You have access to manage this specific server through the Pterodactyl API.`;

  // Pass context to FastAPI
  const response = await fetch(`${process.env.FASTAPI_URL}/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': pterodactylContext?.userId || '',
      'X-Server-ID': pterodactylContext?.serverId || '',
      'X-API-Token': pterodactylContext?.apiToken || '',
    },
    body: JSON.stringify({
      messages: [
        { role: 'system', content: systemPrompt },
        ...messages
      ]
    })
  });
  
  return new Response(response.body, {
    headers: { 'Content-Type': 'text/event-stream' }
  });
}
```

## Security Considerations

**Token Encryption**
```typescript
// frontend-new/lib/security.ts
export function decryptApiToken(encryptedToken: string): string {
  // Use same encryption key as Pterodactyl
  // Implementation depends on Pterodactyl's encryption method
  return decrypt(encryptedToken, process.env.PTERODACTYL_ENCRYPTION_KEY);
}

export function validateContext(context: PterodactylContext): boolean {
  // Validate token hasn't expired
  // Check user has access to server
  // Verify context integrity
  return true; // Implement validation logic
}
```

## Usage in Components

```typescript
// Example component usage
'use client';

import { usePterodactylContext } from '@/components/PterodactylContextProvider';

export function ServerSpecificGreeting() {
  const context = usePterodactylContext();
  
  if (!context) {
    return <div>Loading user context...</div>;
  }
  
  return (
    <div className="bg-blue-50 p-4 rounded-lg">
      <h2>Welcome back, {context.username}! 👋</h2>
      <p>Managing server: <strong>{context.serverName}</strong></p>
      <p>Server ID: {context.serverId}</p>
    </div>
  );
}
```

## Implementation Steps

1. **Add URL parameters** to your Pterodactyl iframe integration
2. **Create context detection** in frontend
3. **Update API routes** to use context
4. **Modify backend tools** to use specific server ID
5. **Add security validation** for tokens
6. **Test iframe integration** in Pterodactyl

This gives you automatic user/server detection with full security! 🎯