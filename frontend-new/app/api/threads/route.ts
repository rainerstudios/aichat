export const runtime = "nodejs";
export const maxDuration = 30;

export async function GET() {
  try {
    const response = await fetch(`${process.env.FASTAPI_URL || 'http://localhost:8000'}/api/chat/threads`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Dev-Mode": "true", // Use dev mode
      },
    });

    if (!response.ok) {
      // If backend is not configured or not accessible, return default thread
      console.warn(`Backend not accessible: ${response.status} ${response.statusText}`);
      return Response.json([{
        thread_id: "default",
        title: "New Chat",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {}
      }]);
    }

    const threads = await response.json();
    
    // If no threads exist, return default thread
    if (!Array.isArray(threads) || threads.length === 0) {
      return Response.json([{
        thread_id: "default",
        title: "New Chat",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {}
      }]);
    }
    
    // Transform to frontend format (keep backend format for compatibility)
    return Response.json(threads);

  } catch (error) {
    console.error('Thread fetch error:', error);
    // Return default thread on error
    return Response.json([{
      thread_id: "default",
      title: "New Chat",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      metadata: {}
    }]);
  }
}

export async function POST(req: Request) {
  try {
    const { title } = await req.json();

    const response = await fetch(`${process.env.FASTAPI_URL || 'http://localhost:8000'}/api/chat/threads`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Dev-Mode": "true", // Use dev mode
      },
      body: JSON.stringify({
        title: title || `Chat ${new Date().toLocaleString()}`,
        metadata: {}
      }),
    });

    if (!response.ok) {
      // If backend is not accessible, create a mock thread
      console.warn(`Backend not accessible for thread creation: ${response.status} ${response.statusText}`);
      const mockThread = {
        thread_id: `thread-${Date.now()}`,
        title: title || "New Chat",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {}
      };
      return Response.json(mockThread);
    }

    const thread = await response.json();
    return Response.json(thread);

  } catch (error) {
    console.error('Thread creation error:', error);
    // Return mock thread on error
    const mockThread = {
      thread_id: `thread-${Date.now()}`,
      title: "New Chat",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      metadata: {}
    };
    return Response.json(mockThread);
  }
}