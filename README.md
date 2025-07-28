# XGaming Server Support - AI Chat Assistant

An AI-powered chat assistant built with Next.js frontend and Python FastAPI backend, specializing in Pterodactyl panel server management and game server hosting support.

## Features

- **Clean Assistant-UI Interface** - Modern chat UI with sidebar navigation
- **Pterodactyl Panel Expertise** - Specialized AI assistant for game server management
- **Real-time Streaming** - Live response streaming for better user experience
- **LangGraph Integration** - Advanced conversation flow management
- **Tool Support** - Extensible tool system for server management tasks

## Architecture

### Frontend (`/frontend`)
- **Next.js 15** with App Router
- **assistant-ui/react** for chat interface
- **Tailwind CSS** for styling
- **TypeScript** for type safety

### Backend (`/backend`)
- **FastAPI** with Python
- **LangGraph** for conversation management
- **OpenAI GPT** integration
- **Assistant-stream** for response streaming

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install poetry
poetry install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Add your OpenAI API key
```

4. Start the backend server:
```bash
python -m app.server
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

## Deployment

The application is deployed with:
- **Frontend**: Next.js running on port 3000
- **Backend**: FastAPI running on port 8000
- **Nginx**: Reverse proxy with SSL termination
- **Domain**: https://chat.xgaming.pro

## License

MIT License
