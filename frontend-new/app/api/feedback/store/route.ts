export const runtime = "nodejs";
export const maxDuration = 30;

export async function POST(req: Request) {
  try {
    const feedbackData = await req.json();

    const response = await fetch(`${process.env.FASTAPI_URL || 'http://localhost:8000'}/api/feedback/store`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(feedbackData),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    return Response.json(result);

  } catch (error) {
    console.error('Feedback submission error:', error);
    return Response.json(
      { error: 'Failed to submit feedback', details: error.message },
      { status: 500 }
    );
  }
}