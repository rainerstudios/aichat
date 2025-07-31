export const runtime = "nodejs";
export const maxDuration = 30;

export async function GET(
  req: Request,
  { params }: { params: { threadId: string } }
) {
  try {
    const { threadId } = params;
    const { searchParams } = new URL(req.url);
    const limit = searchParams.get('limit') || '100';

    const response = await fetch(
      `${process.env.FASTAPI_URL || 'http://localhost:8000'}/api/chat/threads/${threadId}/messages?limit=${limit}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-Dev-Mode": "true", // Use dev mode
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const messages = await response.json();
    
    // Transform to Assistant-UI format
    const formattedMessages = messages.map(message => ({
      id: message.message_id,
      role: message.role,
      content: [{ type: "text", text: message.content }],
      createdAt: message.created_at,
      metadata: message.metadata || {}
    }));
    
    return Response.json(formattedMessages);

  } catch (error) {
    console.error('Thread messages fetch error:', error);
    return Response.json(
      { error: 'Failed to fetch thread messages', details: error.message },
      { status: 500 }
    );
  }
}