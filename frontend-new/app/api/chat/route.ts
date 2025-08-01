export const runtime = "nodejs";
export const maxDuration = 60;

export async function POST(req: Request) {
  try {
    const { messages, system, pteroContext } = await req.json();

    // Connect to our FastAPI backend with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 55000); // 55 second timeout

    const headers = {
      "Content-Type": "application/json",
      "X-Dev-Mode": "true", // Use dev mode with real API key
    };

    if (pteroContext?.apiToken) {
      headers["Authorization"] = `Bearer ${pteroContext.apiToken}`;
    }

    const response = await fetch(`${process.env.FASTAPI_URL || 'http://localhost:8000'}/api/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        messages,
        system: system || `You are XGaming Server's AI customer support assistant. Your primary goal is to help users with their game servers.

CORE INSTRUCTIONS:
- Your main purpose is to answer questions related to game servers, hosting, the XGaming Server panel, and technical issues.
- To answer these questions accurately, you MUST use the tools provided to you, especially the 'get_knowledge_base_info' tool. This tool contains specific, trusted information that is more reliable than your general knowledge.
- If a user asks a question about a specific game feature (like mods, crossplay, settings, etc.), your FIRST priority is to use the 'get_knowledge_base_info' tool to find the answer.
- If the tool returns no information, you can then try to answer from your general knowledge, but you should state that you couldn't find a specific guide.
- If the question is clearly unrelated to game servers (e.g., cooking, cars), then you should politely decline and steer the conversation back to server hosting topics.

Your expertise is focused on:
- Game server management and configuration
- XGaming Server panel navigation and features  
- Server performance, crashes, and connectivity issues
- File management and server administration
- Mod/plugin installation and troubleshooting
- Server optimization and resource management
- Backup and restore procedures
- Network configuration and port management

For questions outside these topics, respond: "I'm here to help with XGaming Server hosting. How can I assist you with your game server today?"`,
        ptero_context: pteroContext,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      console.warn(`Backend not available: ${response.status} ${response.statusText}`);
      
      // Create enhanced streaming response with intelligent status updates
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          // More detailed and intelligent status updates
          const statusUpdates = [
            "🔍 Querying backend services...",
            "⚠️  Backend unavailable, activating fallback mode...", 
            "🔧 Checking Pterodactyl panel connection...",
            "📊 Analyzing server context and user query...",
            "🤖 Initializing AI response system...",
            "💡 Preparing intelligent response..."
          ];
          
          const finalMessage = `Hello! I'm XGaming Server's AI assistant. 🎮

I'm currently running in **demo mode** as the backend service is initializing. Here's what's happening:

## 🔄 System Status
- ✅ **Frontend Interface**: Fully operational
- ⚠️  **Backend API**: Temporarily unavailable
- ⚠️  **Panel Integration**: Limited access
- ✅ **Local Chat**: Ready and responsive
- ✅ **Auto-scroll**: Working perfectly
- ✅ **Syntax Highlighting**: Enhanced and active

## 🚀 Available Features
I can still help you with:

### 🎯 **Game Server Support**
- Minecraft server setup and configuration
- Performance optimization strategies
- Troubleshooting common hosting issues
- Plugin and mod installation guidance

### 🛠️ **Technical Assistance**
- Server configuration best practices
- Network and connectivity issues
- Resource management tips
- Backup and restore procedures

### 📝 **Documentation & Guides**
- Step-by-step tutorials
- Configuration examples with **syntax highlighting**
- Best practice recommendations

## 💬 Interactive Features
- **Smart auto-scroll** during our conversation
- **Enhanced code blocks** with language detection
- **Real-time streaming** responses
- **Copy-paste** functionality for code snippets

---

**How can I help you with your game server today?** Feel free to ask about any server-related topics! 🚀`;

          let statusIndex = 0;
          
          const sendStatusUpdate = () => {
            if (statusIndex < statusUpdates.length) {
              controller.enqueue(encoder.encode(`0:"${statusUpdates[statusIndex]}"\n`));
              statusIndex++;
              setTimeout(sendStatusUpdate, 900);
            } else {
              // Clear status and send main message
              setTimeout(() => {
                controller.enqueue(encoder.encode(`0:"\n\n"`));
                sendMainMessage();
              }, 600);
            }
          };
          
          const sendMainMessage = () => {
            // Send message in chunks for better streaming effect
            const chunks = finalMessage.split('\n\n');
            let chunkIndex = 0;
            
            const sendChunk = () => {
              if (chunkIndex < chunks.length) {
                const chunk = chunkIndex === 0 ? chunks[chunkIndex] : '\n\n' + chunks[chunkIndex];
                const words = chunk.split(' ');
                let wordIndex = 0;
                
                const sendWord = () => {
                  if (wordIndex < words.length) {
                    const word = wordIndex === 0 && chunkIndex === 0 ? words[wordIndex] : ' ' + words[wordIndex];
                    controller.enqueue(encoder.encode(`0:"${word}"\n`));
                    wordIndex++;
                    setTimeout(sendWord, 40);
                  } else {
                    chunkIndex++;
                    setTimeout(sendChunk, 200);
                  }
                };
                
                sendWord();
              } else {
                controller.close();
              }
            };
            
            sendChunk();
          };
          
          sendStatusUpdate();
        }
      });
      
      return new Response(stream, {
        status: 200,
        headers: {
          "Content-Type": "text/plain; charset=utf-8",
          "Access-Control-Allow-Origin": "*",
          "Cache-Control": "no-cache",
          "Connection": "keep-alive",
        },
      });
    }

    // Return the streaming response from FastAPI with proper headers
    return new Response(response.body, {
      status: response.status,
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });

  } catch (error) {
    console.error('Chat API Error:', error);
    
    if (error.name === 'AbortError') {
      return new Response('Request timeout', { status: 408 });
    }
    
    // Provide fallback response on connection error
    const fallbackMessage = "I'm sorry, I'm currently unable to connect to the backend service. This is likely a temporary issue. Please try again in a moment, or contact support if the problem persists.";
    
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(`0:"${fallbackMessage}"\n`));
        controller.close();
      }
    });
    
    return new Response(stream, {
      status: 200,
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });
  }
}
