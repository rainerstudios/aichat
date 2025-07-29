# Chat Persistence Setup with Assistant-UI Cloud

This guide explains how to enable chat persistence using the Assistant-UI Cloud service.

## Quick Setup (Anonymous Users)

The app will work out of the box with basic functionality. To enable chat persistence for anonymous users:

1. **Sign up at Assistant-UI Cloud**
   - Go to [https://cloud.assistant-ui.com/](https://cloud.assistant-ui.com/)
   - Create a new account
   - Create a new project

2. **Get your Frontend API URL**
   - In your project dashboard, go to "Settings"
   - Copy the Frontend API URL (e.g., `https://proj-[ID].assistant-api.com`)

3. **Update Environment Variables**
   ```bash
   # In /var/www/aichat/frontend/.env.local
   NEXT_PUBLIC_ASSISTANT_BASE_URL=https://proj-[YOUR-ID].assistant-api.com
   ```

4. **Restart the Frontend**
   ```bash
   cd /var/www/aichat/frontend
   npm run dev
   ```

That's it! Users will now have persistent chat history tied to their browser session.

## Advanced Setup (Authenticated Users)

For production use with user authentication:

1. **Get API Key**
   - In your Assistant-UI Cloud dashboard, go to "API Keys"
   - Create a new API key
   - Add it to your environment:
   ```bash
   ASSISTANT_API_KEY=your-api-key-here
   ```

2. **Set up Authentication Provider**
   - In the dashboard, go to "Auth Integrations"
   - Add your auth provider (Clerk, Auth0, Supabase, etc.)
   - Follow the provider-specific setup instructions

3. **Update Runtime Provider**
   - Replace `AnonymousCloudProvider` with `CloudRuntimeProvider` in `app/page.tsx`
   - This enables full thread management with user-specific workspaces

## Features Enabled

✅ **Thread Persistence** - Chat history is automatically saved  
✅ **Thread List** - Users can see and switch between conversations  
✅ **Cross-Device Sync** - (With auth) Access chats from any device  
✅ **Automatic Titles** - AI generates conversation titles  
✅ **Thread Management** - Create, delete, and organize conversations  

## Current Implementation

The app currently uses:
- **Anonymous Cloud Provider** - Simple browser-session persistence
- **Thread List Sidebar** - Shows chat history in left panel
- **Pterodactyl Expertise** - AI specialized for game server support
- **Real-time Streaming** - Live response updates

## Troubleshooting

**No thread history showing?**
- Check that `NEXT_PUBLIC_ASSISTANT_BASE_URL` is set correctly
- Verify the URL is accessible from your browser
- Check browser console for any errors

**Authentication issues?**
- Ensure `ASSISTANT_API_KEY` is set in backend environment
- Verify auth provider configuration matches dashboard settings
- Check that token endpoint is accessible

**Threads not persisting?**
- Confirm cloud service is properly configured
- Check network requests in browser dev tools
- Verify API endpoints are responding correctly

## Migration from Local to Cloud

If you're upgrading from local-only chat:
1. Existing sessions will continue to work locally
2. New sessions will use cloud persistence
3. No data loss - users just get enhanced functionality
4. Can switch back by removing environment variables