# AI Assistant Project Implementation Plan
**Pterodactyl Panel Integration with RAG, LLM, and Multi-API Support**

## 🎯 Project Overview

Building a comprehensive AI assistant that integrates with:
- **RAG System**: Trieve for knowledge base and document search
- **LLM**: GPT-4 API for intelligent responses
- **Pterodactyl API**: Server management, logs, diagnostics
- **WHMCS API**: Billing and account management
- **Deployment**: Iframe embedded in existing Pterodactyl panel

## 🏗️ Architecture Overview

```
Frontend (iframe) → FastAPI Backend → LangGraph Agent
                                    ├── RAG (Trieve)
                                    ├── LLM (GPT-4)
                                    ├── Pterodactyl API
                                    └── WHMCS API
```

## 📁 Project Structure

```
your-assistant/
├── backend/
│   ├── app/
│   │   ├── langgraph/
│   │   │   ├── agent.py          # Main agent workflow
│   │   │   ├── tools.py          # All API tools
│   │   │   └── state.py          # Agent state management
│   │   ├── api/
│   │   │   ├── pterodactyl.py    # Pterodactyl API client
│   │   │   ├── whmcs.py          # WHMCS API client
│   │   │   └── trieve_rag.py     # RAG implementation
│   │   ├── auth/
│   │   │   └── security.py       # User context & permissions
│   │   ├── models/
│   │   │   └── schemas.py        # Pydantic models
│   │   └── server.py             # FastAPI server
├── frontend/
│   ├── app/
│   │   ├── iframe/               # Iframe-specific components
│   │   ├── components/
│   │   └── page.tsx
├── docs/
│   ├── api-documentation.md
│   └── deployment-guide.md
└── docker/
    ├── Dockerfile.backend
    ├── Dockerfile.frontend
    └── docker-compose.yml
```

## 🚀 Implementation Steps

### Phase 1: Foundation Setup (Week 1)

#### Step 1.1: Project Initialization
```bash
# Clone base repository
git clone https://github.com/Yonom/assistant-ui-langgraph-fastapi.git your-assistant
cd your-assistant

# Backend setup
cd backend
poetry install
poetry add trieve-langchain langchain-openai python-multipart

# Frontend setup  
cd ../frontend
yarn install
```

#### Step 1.2: Environment Configuration
Create `.env` files:

**Backend (.env)**:
```env
# LLM
OPENAI_API_KEY=your_openai_key

# Trieve RAG
TRIEVE_API_KEY=your_trieve_key
TRIEVE_BASE_URL=https://api.trieve.ai
TRIEVE_COLLECTION_ID=your_collection_id

# Pterodactyl (admin application key for service)
PTERODACTYL_URL=https://your-panel.com
PTERODACTYL_ADMIN_KEY=your_admin_key

# WHMCS
WHMCS_URL=https://your-whmcs.com
WHMCS_API_IDENTIFIER=your_identifier
WHMCS_API_SECRET=your_secret

# Security
JWT_SECRET=your_jwt_secret
CORS_ORIGINS=["https://your-panel.com"]
```

**Frontend (.env.local)**:
```env
NEXT_PUBLIC_API_URL=https://your-backend.com
NEXT_PUBLIC_IFRAME_MODE=true
```

### Phase 2: API Integrations (Week 2)

#### Step 2.1: Pterodactyl API Client

**File: `backend/app/api/pterodactyl.py`**
```python
import requests
from typing import Dict, List, Optional
import logging

class PterodactylAPI:
    def __init__(self, base_url: str, admin_key: str):
        self.base_url = base_url.rstrip('/')
        self.admin_headers = {
            "Authorization": f"Bearer {admin_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def get_user_context(self, user_session_token: str) -> Dict:
        """Validate user session and get their context"""
        # Implement session validation
        pass
    
    def get_user_servers(self, user_id: int) -> List[Dict]:
        """Get servers for specific user"""
        pass
    
    def get_server_details(self, server_id: str, user_id: int) -> Dict:
        """Get server details with ownership check"""
        pass
    
    def get_server_logs(self, server_id: str, user_id: int, lines: int = 100) -> str:
        """Fetch recent server logs"""
        pass
    
    def restart_server(self, server_id: str, user_id: int) -> bool:
        """Restart server with permission check"""
        pass
```

#### Step 2.2: WHMCS API Client

**File: `backend/app/api/whmcs.py`**
```python
import requests
import hashlib
from typing import Dict, Optional

class WHMCSAPI:
    def __init__(self, url: str, identifier: str, secret: str):
        self.url = url.rstrip('/')
        self.identifier = identifier
        self.secret = secret
    
    def get_client_details(self, email: str) -> Optional[Dict]:
        """Get client details by email"""
        pass
    
    def get_client_products(self, client_id: int) -> List[Dict]:
        """Get client's active products/services"""
        pass
    
    def check_service_status(self, service_id: int) -> Dict:
        """Check if service is active, suspended, etc."""
        pass
```

#### Step 2.3: Trieve RAG Integration

**File: `backend/app/api/trieve_rag.py`**
```python
from trieve_langchain import TrieveRetriever
from typing import List, Dict

class TrieveRAG:
    def __init__(self, api_key: str, base_url: str, collection_id: str):
        self.retriever = TrieveRetriever(
            api_key=api_key,
            base_url=base_url,
            collection_id=collection_id
        )
    
    def search_knowledge(self, query: str, k: int = 5) -> List[Dict]:
        """Search knowledge base for relevant documents"""
        docs = self.retriever.get_relevant_documents(query, k=k)
        return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
    
    def get_troubleshooting_context(self, error_message: str) -> str:
        """Get troubleshooting context for specific error"""
        pass
```

### Phase 3: LangGraph Agent Implementation (Week 3)

#### Step 3.1: Agent Tools

**File: `backend/app/langgraph/tools.py`**
```python
from langchain_core.tools import tool
from typing import Dict, List
from ..api.pterodactyl import PterodactylAPI
from ..api.whmcs import WHMCSAPI
from ..api.trieve_rag import TrieveRAG

# Initialize APIs (should be dependency injected in production)
pterodactyl = PterodactylAPI(...)
whmcs = WHMCSAPI(...)
rag = TrieveRAG(...)

@tool
def get_server_status(server_id: str, user_context: Dict) -> Dict:
    """Get current server status and basic info"""
    return pterodactyl.get_server_details(server_id, user_context["user_id"])

@tool  
def analyze_server_logs(server_id: str, user_context: Dict) -> str:
    """Fetch and analyze recent server logs for issues"""
    logs = pterodactyl.get_server_logs(server_id, user_context["user_id"])
    # Add log analysis logic here
    return f"Log analysis: {logs[:500]}..."

@tool
def search_knowledge_base(query: str) -> List[Dict]:
    """Search documentation and troubleshooting guides"""
    return rag.search_knowledge(query)

@tool
def check_billing_status(user_context: Dict) -> Dict:
    """Check user's billing and service status"""
    client = whmcs.get_client_details(user_context["email"])
    return whmcs.check_service_status(client["id"]) if client else {}

@tool
def restart_server_confirmed(server_id: str, user_context: Dict) -> str:
    """Restart server after confirmation"""
    success = pterodactyl.restart_server(server_id, user_context["user_id"])
    return "Server restarted successfully" if success else "Failed to restart server"
```

#### Step 3.2: Agent Workflow

**File: `backend/app/langgraph/agent.py`**
```python
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from typing import Dict, List, TypedDict
import json

class AgentState(TypedDict):
    messages: List[Dict]
    user_context: Dict
    current_server: str
    retrieved_docs: List[Dict]
    confirmation_pending: bool
    action_type: str

llm = ChatOpenAI(model="gpt-4", temperature=0)

def analyze_intent(state: AgentState, config) -> AgentState:
    """Analyze user intent and route accordingly"""
    user_message = state["messages"][-1]["content"]
    
    # Simple intent classification (enhance with better NLU)
    if any(word in user_message.lower() for word in ["broken", "error", "not working", "issue"]):
        state["action_type"] = "troubleshoot"
    elif any(word in user_message.lower() for word in ["restart", "reboot", "kill"]):
        state["action_type"] = "server_action"
    elif any(word in user_message.lower() for word in ["billing", "payment", "invoice"]):
        state["action_type"] = "billing"
    else:
        state["action_type"] = "general"
    
    return state

def retrieve_context(state: AgentState, config) -> AgentState:
    """Retrieve relevant context based on intent"""
    query = state["messages"][-1]["content"]
    
    if state["action_type"] in ["troubleshoot", "general"]:
        # Search knowledge base
        docs = rag.search_knowledge(query)
        state["retrieved_docs"] = docs
    
    return state

def troubleshoot_flow(state: AgentState, config) -> AgentState:
    """Handle server troubleshooting"""
    if not state.get("current_server"):
        # Ask user to specify server
        response = "Which server are you having issues with? Please provide the server name or ID."
    else:
        # Get server logs and analyze
        logs = analyze_server_logs(state["current_server"], state["user_context"])
        context = "\n".join([doc["content"] for doc in state["retrieved_docs"]])
        
        prompt = f"""
        Server logs: {logs}
        
        Troubleshooting context: {context}
        
        Analyze the logs and provide specific troubleshooting steps.
        """
        response = llm.invoke(prompt).content
    
    state["messages"].append({"role": "assistant", "content": response})
    return state

def confirmation_flow(state: AgentState, config) -> AgentState:
    """Handle confirmations for destructive actions"""
    user_message = state["messages"][-1]["content"].lower()
    
    if "yes" in user_message or "confirm" in user_message:
        # Execute the action
        if state["action_type"] == "server_action":
            result = restart_server_confirmed(state["current_server"], state["user_context"])
            state["messages"].append({"role": "assistant", "content": result})
        state["confirmation_pending"] = False
    else:
        state["messages"].append({"role": "assistant", "content": "Action cancelled."})
        state["confirmation_pending"] = False
    
    return state

def llm_response(state: AgentState, config) -> AgentState:
    """Generate LLM response with context"""
    user_message = state["messages"][-1]["content"]
    context = "\n".join([doc["content"] for doc in state.get("retrieved_docs", [])])
    
    system_prompt = f"""
    You are a helpful server support assistant. 
    
    Context from knowledge base:
    {context}
    
    Guidelines:
    - Be helpful and accurate
    - For server actions, always ask for confirmation
    - Provide step-by-step troubleshooting
    - Don't mention external website names
    """
    
    messages = [{"role": "system", "content": system_prompt}] + state["messages"]
    response = llm.invoke(messages).content
    
    # Check if confirmation needed
    if any(word in user_message.lower() for word in ["restart", "stop", "kill"]):
        response += "\n\nDo you want me to proceed with this action? Please confirm."
        state["confirmation_pending"] = True
    
    state["messages"].append({"role": "assistant", "content": response})
    return state

# Build the graph
workflow = StateGraph(AgentState)

workflow.add_node("analyze_intent", analyze_intent)
workflow.add_node("retrieve_context", retrieve_context)
workflow.add_node("troubleshoot", troubleshoot_flow)
workflow.add_node("confirmation", confirmation_flow)
workflow.add_node("llm_response", llm_response)

workflow.set_entry_point("analyze_intent")

# Add conditional edges
workflow.add_edge("analyze_intent", "retrieve_context")
workflow.add_conditional_edges(
    "retrieve_context",
    lambda state: state["action_type"],
    {
        "troubleshoot": "troubleshoot",
        "server_action": "llm_response",
        "billing": "llm_response", 
        "general": "llm_response"
    }
)

workflow.add_conditional_edges(
    "llm_response",
    lambda state: "confirmation" if state.get("confirmation_pending") else END,
    {
        "confirmation": "confirmation",
        END: END
    }
)

workflow.add_edge("troubleshoot", END)
workflow.add_edge("confirmation", END)

agent = workflow.compile()
```

### Phase 4: Iframe Integration (Week 4)

#### Step 4.1: Frontend Iframe Mode

**File: `frontend/app/iframe/page.tsx`**
```tsx
'use client'

import { AssistantRuntimeProvider } from '@assistant-ui/react'
import { Thread } from '@assistant-ui/react'
import { useLangGraphRuntime } from '../lib/langgraph-runtime'
import { usePostMessage } from '../hooks/usePostMessage'

export default function IframePage() {
  const { userContext } = usePostMessage()
  
  const runtime = useLangGraphRuntime({
    apiUrl: process.env.NEXT_PUBLIC_API_URL,
    userContext: userContext
  })

  return (
    <div className="h-screen w-full bg-white">
      <AssistantRuntimeProvider runtime={runtime}>
        <div className="flex flex-col h-full">
          <div className="bg-blue-600 text-white p-4">
            <h1 className="text-lg font-semibold">AI Support Assistant</h1>
          </div>
          <div className="flex-1 overflow-hidden">
            <Thread />
          </div>
        </div>
      </AssistantRuntimeProvider>
    </div>
  )
}
```

#### Step 4.2: Parent-Iframe Communication

**File: `frontend/hooks/usePostMessage.ts`**
```typescript
import { useEffect, useState } from 'react'

interface UserContext {
  userId: number
  email: string
  sessionToken: string
  serverIds: string[]
}

export function usePostMessage() {
  const [userContext, setUserContext] = useState<UserContext | null>(null)

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return
      
      if (event.data.type === 'USER_CONTEXT') {
        setUserContext(event.data.payload)
      }
    }

    window.addEventListener('message', handleMessage)
    
    // Request initial context
    window.parent.postMessage({ type: 'REQUEST_CONTEXT' }, '*')

    return () => window.removeEventListener('message', handleMessage)
  }, [])

  return { userContext }
}
```

#### Step 4.3: Pterodactyl Panel Integration

**File to add to your Pterodactyl panel: `resources/views/server/ai-assistant.blade.php`**
```blade
@extends('layouts.admin')

@section('title')
    AI Assistant
@endsection

@section('content-header')
    <h1>AI Support Assistant</h1>
@endsection

@section('content')
<div class="row">
    <div class="col-xs-12">
        <div class="box box-primary">
            <div class="box-body">
                <iframe 
                    id="ai-assistant-frame"
                    src="{{ config('app.ai_assistant_url') }}/iframe"
                    width="100%" 
                    height="600px"
                    frameborder="0">
                </iframe>
            </div>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const iframe = document.getElementById('ai-assistant-frame');
    const userContext = {
        userId: {{ Auth::user()->id }},
        email: "{{ Auth::user()->email }}",
        sessionToken: "{{ session('pterodactyl_session') }}",
        serverIds: @json(Auth::user()->servers->pluck('identifier'))
    };

    iframe.onload = function() {
        iframe.contentWindow.postMessage({
            type: 'USER_CONTEXT',
            payload: userContext
        }, '*');
    };

    window.addEventListener('message', function(event) {
        if (event.data.type === 'REQUEST_CONTEXT') {
            iframe.contentWindow.postMessage({
                type: 'USER_CONTEXT', 
                payload: userContext
            }, '*');
        }
    });
});
</script>
@endsection
```

### Phase 5: Knowledge Base Setup (Week 5)

#### Step 5.1: Document Ingestion Pipeline

**File: `scripts/ingest_docs.py`**
```python
import os
from chunkr import chunkr_pdf
from trieve import TrieveClient

def ingest_documentation():
    """Ingest all documentation into Trieve"""
    client = TrieveClient(
        api_key=os.getenv("TRIEVE_API_KEY"),
        base_url=os.getenv("TRIEVE_BASE_URL")
    )
    
    # Ingest PDFs
    pdf_files = ["game-guides/", "troubleshooting/", "server-setup/"]
    for pdf_dir in pdf_files:
        for file in os.listdir(pdf_dir):
            if file.endswith('.pdf'):
                chunks = chunkr_pdf(os.path.join(pdf_dir, file))
                client.upload_chunks(chunks)
    
    print("Documentation ingested successfully")

if __name__ == "__main__":
    ingest_documentation()
```

### Phase 6: Security & Production (Week 6)

#### Step 6.1: Security Implementation

**File: `backend/app/auth/security.py`**
```python
from fastapi import HTTPException, Depends, Header
from typing import Optional, Dict
import jwt
from .pterodactyl import PterodactylAPI

async def get_user_context(authorization: Optional[str] = Header(None)) -> Dict:
    """Extract and validate user context from request"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    try:
        # Validate session with Pterodactyl
        token = authorization.replace("Bearer ", "")
        user_context = pterodactyl.get_user_context(token)
        return user_context
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")

def check_server_permission(server_id: str, user_context: Dict) -> bool:
    """Check if user has permission for server"""
    return server_id in user_context.get("server_ids", [])
```

#### Step 6.2: Production Configuration

**File: `docker/docker-compose.yml`**
```yaml
version: '3.8'

services:
  backend:
    build: 
      context: ../backend
      dockerfile: ../docker/Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - TRIEVE_API_KEY=${TRIEVE_API_KEY}
      - PTERODACTYL_URL=${PTERODACTYL_URL}
      - WHMCS_URL=${WHMCS_URL}
    volumes:
      - ../logs:/app/logs

  frontend:
    build:
      context: ../frontend  
      dockerfile: ../docker/Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - frontend
```

## 🚦 Testing Strategy

### Unit Tests
- API client tests
- Tool function tests  
- Agent workflow tests

### Integration Tests
- End-to-end user flows
- API authentication
- Iframe communication

### Load Tests
- Concurrent user handling
- API rate limiting
- Response time optimization

## 📊 Monitoring & Analytics

### Logging
```python
# backend/app/utils/logging.py
import logging
import json
from datetime import datetime

class AIAssistantLogger:
    def __init__(self):
        self.logger = logging.getLogger("ai_assistant")
        
    def log_interaction(self, user_id: int, query: str, response: str, tools_used: list):
        """Log user interactions for analysis"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "query": query,
            "response": response,
            "tools_used": tools_used
        }
        self.logger.info(json.dumps(log_data))
```

### Metrics
- Response time per query type
- Most common issues/questions
- Tool usage statistics
- User satisfaction scores

## 🔧 Deployment Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] SSL certificates installed  
- [ ] Database backups scheduled
- [ ] Monitoring setup complete
- [ ] Load testing passed

### Security Checklist
- [ ] API rate limiting enabled
- [ ] User permission validation working
- [ ] Sensitive data not logged
- [ ] CORS properly configured
- [ ] Input sanitization implemented

### Post-deployment
- [ ] Health checks passing
- [ ] Logs flowing correctly
- [ ] Backup verification
- [ ] Performance monitoring active
- [ ] User acceptance testing

## 📈 Future Enhancements

### Phase 7: Advanced Features
- Multi-language support
- Voice interface
- Mobile app version
- Advanced analytics dashboard
- Machine learning for issue prediction

### Phase 8: Enterprise Features  
- Multi-tenant support
- Advanced RBAC
- Audit compliance
- Custom branding
- API rate limiting per user

## 📚 Documentation

### API Documentation
- OpenAPI/Swagger docs
- Integration guides
- Troubleshooting guides

### User Documentation
- Getting started guide
- Feature overview
- FAQ section

---

## 🎯 Success Metrics

### Technical Metrics
- Response time < 2 seconds
- 99.9% uptime
- Zero security incidents

### Business Metrics  
- 50% reduction in support tickets
- 90% user satisfaction
- 80% issue resolution without human intervention

---

**Next Steps**: Start with Phase 1 foundation setup and work through each phase systematically. Each phase builds on the previous one and can be deployed incrementally.