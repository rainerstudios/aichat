# Environment Setup for AI Chat Assistant

This document outlines all required environment variables for the AI chat assistant with Pterodactyl integration, Cloudflare AutoRAG, and Firecrawl.

## Required Environment Variables

### Core Application
```bash
# FastAPI and general app settings
PYTHONPATH=/var/www/aichat/backend
ENVIRONMENT=production  # or development
DEBUG=false
```

### Pterodactyl Integration
```bash
# Pterodactyl Panel Configuration
PTERODACTYL_PANEL_URL=https://panel.xgaming.pro
PTERODACTYL_ADMIN_API_KEY=your_application_api_key_here

# Note: The admin API key should have MINIMAL permissions:
# - users.view (to lookup users and their servers)
# - servers.view (to get server details)
# - servers.power (to start/stop/restart servers)
# - servers.console (to send console commands)
# DO NOT grant: servers.create, servers.delete, users.create, users.delete
```

### Cloudflare AutoRAG
```bash
# Cloudflare Account and AutoRAG Configuration
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
CLOUDFLARE_AUTORAG_INSTANCE_ID=your_autorag_instance_id

# Cloudflare R2 for document storage
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET_NAME=xgaming-docs-autorag
```

### Firecrawl Documentation Crawling
```bash
# Firecrawl API for documentation crawling
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

### OpenAI for LLM
```bash
# OpenAI API for the language model
OPENAI_API_KEY=your_openai_api_key
```

### Database (if using)
```bash
# Database configuration (adjust as needed)
DATABASE_URL=postgresql://user:password@localhost/aichat
```

## Setup Instructions

### 1. Pterodactyl Admin API Key Setup

1. Log into your Pterodactyl panel as an administrator
2. Go to Admin Panel → API → Application
3. Create a new API key with these permissions:
   - `users.view`
   - `servers.view` 
   - `servers.power`
   - `servers.console`
4. Copy the key and set `PTERODACTYL_ADMIN_API_KEY`

### 2. Cloudflare AutoRAG Setup

1. Log into Cloudflare Dashboard
2. Go to AI → AutoRAG
3. Create a new AutoRAG instance
4. Note the instance ID and set `CLOUDFLARE_AUTORAG_INSTANCE_ID`
5. Create an R2 bucket for document storage
6. Generate R2 API tokens with read/write access to the bucket

### 3. Firecrawl Setup

1. Sign up at [firecrawl.dev](https://firecrawl.dev)
2. Get your API key from the dashboard
3. Set `FIRECRAWL_API_KEY`

### 4. Environment File Creation

Create a `.env` file in `/var/www/aichat/backend/`:

```bash
# Copy the template above and fill in your actual values
cp .env.example .env
# Edit with your values
nano .env
```

### 5. Populate AutoRAG with Documentation

After setting up environment variables, run:

```bash
cd /var/www/aichat/backend/app
python scripts/populate_autorag.py
```

This will:
- Crawl documentation from multiple game server sources using Firecrawl
- Include metadata for game types (Minecraft, Arma Reforger, Rust, CS2, etc.)
- Upload the documents to your R2 bucket with proper categorization
- AutoRAG will automatically index them for intelligent retrieval

The system now crawls documentation from:
- Pterodactyl Panel and Wings documentation
- Minecraft (Paper, Spigot, vanilla server guides)
- Arma Reforger server hosting
- Rust server setup
- Counter-Strike 2 dedicated servers
- Valheim server setup
- General game server performance guides

### 6. Verify Setup

Test your configuration:

```bash
# Test Pterodactyl connection
python -c "
from app.services.pterodactyl_admin_client import create_pterodactyl_admin_client
import asyncio
async def test():
    client = create_pterodactyl_admin_client()
    result = await client.test_connection()
    print(f'Pterodactyl connection: {result}')
asyncio.run(test())
"

# Test AutoRAG connection
python -c "
from app.services.cloudflare_autorag import create_autorag_service
import asyncio
async def test():
    async with create_autorag_service() as service:
        result = await service.get_status()
        print(f'AutoRAG status: {result}')
asyncio.run(test())
"
```

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use strong, unique API keys** for all services
3. **Regularly rotate API keys**, especially the Pterodactyl admin key
4. **Monitor API usage** through service dashboards
5. **Use least-privilege permissions** for all API keys
6. **Keep environment variables secure** in production (use proper secrets management)

## Troubleshooting

### Common Issues

1. **Pterodactyl API errors**: Check that your admin API key has correct permissions
2. **AutoRAG not finding documents**: Ensure R2 bucket is correctly configured and documents are uploaded
3. **Firecrawl timeout errors**: Some sites may take longer to crawl; adjust timeout settings
4. **Import errors**: Make sure `PYTHONPATH` is set correctly

### Logging

Enable debug logging by setting:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

This will provide detailed logs for troubleshooting API calls and integrations.