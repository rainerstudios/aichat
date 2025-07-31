# XGaming AI Chat - Quick Start Guide

This application combines a FastAPI backend with a Next.js frontend using AI SDK for chat functionality.

## Architecture

- **Backend**: FastAPI with LangGraph for AI chat, PostgreSQL for persistence
- **Frontend**: Next.js with Assistant-UI and AI SDK integration
- **AI Integration**: OpenAI with tool calling capabilities
- **Threading**: Full thread persistence with local database

## Quick Start

### 1. Install Dependencies

```bash
# Install backend dependencies
cd backend
pip install -r requirements_clean.txt

# Install frontend dependencies
cd ../frontend-new
npm install
```

### 2. Set Up Environment

**Backend** (`backend/.env`):
```
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql+asyncpg://username:password@localhost/dbname
```

**Frontend** (`frontend-new/.env.local`):
```
FASTAPI_URL=http://localhost:8000
```

### 3. Start the Application

```bash
# From the root directory
npm run dev
```

This will start both:
- Backend API: http://localhost:8000
- Frontend App: http://localhost:3000

### 4. Alternative: Start Services Separately

**Backend only:**
```bash
npm run backend
# Or directly: cd backend && python -m app.server
```

**Frontend only:**
```bash
npm run frontend  
# Or directly: cd frontend-new && npm run dev
```

## API Endpoints

### Chat
- `POST /api/chat` - Main chat endpoint with streaming
- `GET /api/chat/health` - Health check

### Threads (AI SDK compatible)
- `GET /api/threads` - Get user threads
- `POST /api/threads` - Create new thread
- `GET /api/threads/{id}/messages` - Get thread messages
- `POST /api/threads/{id}/messages` - Add message to thread

### Legacy Thread Management
- `GET /api/chat/threads` - Original thread endpoints
- `POST /api/chat/threads` - Create thread (legacy format)

## Troubleshooting

### Backend Issues
- Check database connection in `.env`
- Verify OpenAI API key is valid
- Ensure all dependencies are installed

### Frontend Issues
- Verify `FASTAPI_URL` in `.env.local`
- Check that backend is running on port 8000
- Clear Next.js cache: `rm -rf .next`

### Thread Issues
- Threads are persisted in PostgreSQL
- Check database tables: `chat_threads`, `chat_messages`
- Verify user authentication is working

## Development

- Backend uses FastAPI with auto-reload
- Frontend uses Next.js with Turbopack for fast development
- Both services support hot reloading during development

## Production Deployment

1. Set up PostgreSQL database
2. Configure environment variables
3. Build frontend: `cd frontend-new && npm run build`
4. Start backend: `cd backend && python -m app.server`
5. Start frontend: `cd frontend-new && npm start`