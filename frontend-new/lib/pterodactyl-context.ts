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
