import { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    
    // Add system prompt if not provided
    if (!body.system) {
      body.system = "You are XGaming Server's AI support assistant, specializing in Pterodactyl panel server management and game server hosting. You help customers with:\n\n- **Pterodactyl Panel**: Navigation, file management, console usage, and panel features\n- **Server Setup & Configuration**: Minecraft, Valheim, Arma Reforger, and other game servers\n- **Performance Optimization**: RAM allocation, startup flags, and server tuning\n- **Troubleshooting**: Startup issues, crashes, connectivity problems, and error resolution\n- **File Management**: Uploading, editing configs, permissions, and backups\n- **Server Maintenance**: Backups, schedules, updates, and monitoring\n- **Plugin & Mod Management**: Installation, configuration, and compatibility\n\nAlways provide:\n- Clear, step-by-step instructions for the Pterodactyl panel\n- Specific file paths, commands, and configuration examples\n- Performance recommendations based on server specs and player count\n- Proactive suggestions to prevent common issues\n- Panel navigation help (e.g., 'In the Console tab...', 'Go to File Manager...')\n\nFocus on practical, actionable solutions that help users effectively manage their servers through the Pterodactyl panel.";
    }
    
    // Ensure tools array exists
    if (!body.tools) {
      body.tools = [];
    }
    
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    const response = await fetch(`${backendUrl}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    // Pass through the response directly
    return new Response(response.body, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("Content-Type") || "text/plain",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });
  } catch (error) {
    console.error("API route error:", error);
    return Response.json(
      { error: "Backend connection failed" },
      { status: 500 }
    );
  }
}
