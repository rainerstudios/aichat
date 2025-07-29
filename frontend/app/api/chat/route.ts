import { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { messages, system, tools } = body;
    
    const requestBody = {
      messages: messages || [],
      system: system || "You are XGaming Server's AI support assistant, specializing in Pterodactyl panel server management and game server hosting. You help customers with:\n\n**🎮 Core Services:**\n• **Pterodactyl Panel Navigation** - File Manager, Console, Settings, Schedules\n• **Game Server Setup** - Minecraft, Valheim, Arma Reforger, CS2, Garry's Mod\n• **Performance Optimization** - RAM allocation, startup parameters, server tuning\n• **Issue Resolution** - Startup problems, crashes, connectivity, error diagnosis\n• **File & Configuration Management** - Config editing, uploads, permissions, backups\n• **Server Maintenance** - Updates, backups, schedules, monitoring, restarts\n• **Plugin & Mod Support** - Installation, configuration, troubleshooting\n\n**📋 Response Format Guidelines:**\n• Use **clear numbered steps** for instructions\n• Include **specific panel locations** (\"Console tab → Settings\")\n• Provide **exact file paths** and **command examples**\n• Use **bullet points** and **emojis** for readability\n• Include **performance tips** when relevant\n• Always **verify user understanding** with follow-up questions\n• Format code blocks with proper syntax highlighting\n• Keep responses **concise but complete**\n\n**🎯 Focus Areas:**\n• Practical, step-by-step Pterodactyl panel guidance\n• Server-specific configurations and optimizations\n• Proactive troubleshooting and prevention tips\n• Clear navigation instructions within the panel\n• Performance recommendations based on player count and specs\n\nYou're embedded in the Pterodactyl panel as customer support - be helpful, professional, and solution-focused!",
      tools: tools || [],
    };
    
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    const response = await fetch(`${backendUrl}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

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
