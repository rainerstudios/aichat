export const runtime = "nodejs";
export const maxDuration = 60;

export async function POST(req: Request) {
  try {
    const { message, thread_id, user_id, model, context } = await req.json();

    // Connect to our FastAPI backend streaming endpoint
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 55000);

    const headers = {
      "Content-Type": "application/json",
    };

    if (context?.pteroContext?.apiToken) {
      headers["Authorization"] = `Bearer ${context.pteroContext.apiToken}`;
    }

    const response = await fetch(`${process.env.FASTAPI_URL || 'http://localhost:8000'}/api/chat/stream`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        message,
        thread_id,
        user_id,
        model: model || "gpt-4o-mini",
        stream: true,
        context: context?.pteroContext
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    // Return the streaming response from FastAPI with proper SSE headers
    return new Response(response.body, {
      status: response.status,
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
      },
    });

  } catch (error) {
    console.error('Streaming Chat API Error:', error);
    
    if (error.name === 'AbortError') {
      return new Response('Request timeout', { status: 408 });
    }
    
    // Return error as SSE event
    const errorEvent = `data: ${JSON.stringify({
      event_type: "error",
      data: { 
        error: error.message || 'Backend connection failed',
        error_id: `error-${Date.now()}`
      },
      timestamp: Date.now() / 1000
    })}\n\n`;
    
    return new Response(errorEvent, {
      status: 200, // SSE should return 200 even for errors
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });
  }
}