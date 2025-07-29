# Pterodactyl API Endpoints

This document outlines all available API endpoints for this heavily modified Pterodactyl panel, including standard and custom extension routes.

---

### Client API Endpoints (`/api/client`)

These endpoints are for managing servers and account details from a user's perspective.

#### **Standard Routes**

*   **General**
    *   `GET /`: General API information.
    *   `GET /permissions`: List your current API key permissions.
    *   `GET /servers`: List all servers you have access to.
*   **Account**
    *   `GET /account`: Get your account details.
    *   `PUT /account/email`: Update your email address.
    *   `PUT /account/password`: Update your password.
    *   `GET /account/activity`: Get your account activity log.
    *   `GET /account/two-factor`: Get 2FA details.
    *   `POST /account/two-factor`: Enable 2FA.
    *   `POST /account/two-factor/disable`: Disable 2FA.
*   **API Keys**
    *   `GET /account/api-keys`: List your API keys.
    *   `POST /account/api-keys`: Create a new API key.
    *   `DELETE /account/api-keys/{identifier}`: Delete an API key.
*   **SSH Keys**
    *   `GET /account/ssh-keys`: List your SSH keys.
    *   `POST /account/ssh-keys`: Add an SSH key.
    *   `POST /account/ssh-keys/remove`: Remove an SSH key.

#### **Server-Specific Routes (`/servers/{serverIdentifier}` prefix)**

*   **Server Control**
    *   `GET /`: Get server details.
    *   `GET /resources`: Get server resource utilization (CPU, RAM, disk).
    *   `GET /websocket`: Get credentials for the server's websocket.
    *   `POST /power`: Send a power signal (start, stop, kill, restart).
    *   `POST /command`: Send a command to the server console.
*   **Files**
    *   `GET /files/list`: List files in a directory.
    *   `GET /files/contents`: Get the content of a file.
    *   `GET /files/download`: Get a download link for a file.
    *   `POST /files/write`: Write to a file.
    *   `POST /files/copy`: Copy a file.
    *   `PUT /files/rename`: Rename a file or folder.
    *   `POST /files/compress`: Compress files.
    *   `POST /files/decompress`: Decompress a file.
    *   `POST /files/delete`: Delete files/folders.
    *   `POST /files/create-folder`: Create a new directory.
    *   `POST /pull`: Pull a file from a remote URL.
    *   `GET /upload`: Generate a one-time URL for file uploads.
*   **Databases**
    *   `GET /databases`: List server databases.
    *   `POST /databases`: Create a new database.
    *   `DELETE /databases/{database}`: Delete a database.
    *   `POST /databases/{database}/rotate-password`: Generate a new password for a database.
*   **Backups**
    *   `GET /backups`: List all server backups.
    *   `POST /backups`: Create a new backup.
    *   `GET /backups/{backup}`: Get details for a specific backup.
    *   `GET /backups/{backup}/download`: Get a download link for a backup.
    *   `POST /backups/{backup}/restore`: Restore a backup.
    *   `POST /backups/{backup}/lock`: Lock or unlock a backup.
    *   `DELETE /backups/{backup}`: Delete a backup.
*   **Users**
    *   `GET /users`: List sub-users.
    *   `POST /users`: Create a new sub-user.
    *   `GET /users/{user}`: View a specific sub-user.
    *   `POST /users/{user}`: Update a sub-user.
    *   `DELETE /users/{user}`: Delete a sub-user.
*   **Settings**
    *   `POST /settings/rename`: Rename the server.
    *   `POST /settings/reinstall`: Reinstall the server.
    *   `PUT /settings/docker-image`: Change the server's Docker image.
*   **Startup & Variables**
    *   `GET /startup`: List startup variables.
    *   `PUT /startup/variable`: Update a startup variable.
*   **Network**
    *   `GET /network/allocations`: List network allocations.
    *   `POST /network/allocations`: Create a new allocation.
    *   `POST /network/allocations/{allocation}/primary`: Set a primary allocation.
    *   `DELETE /network/allocations/{allocation}`: Delete an allocation.

---

### **Modified & Extension Routes**

These endpoints are from your custom modifications.

*   **Egg Changer (`/extensions/eggchanger/servers/{serverIdentifier}` prefix)**
    *   `GET /`: Get available egg change options.
    *   `GET /nests`: List all available nests.
    *   `PATCH /`: Change the server's egg.
*   **File Search (`/extensions/filesearch/servers/{serverIdentifier}` prefix)**
    *   `POST /search`: Search for files within the server.
*   **Minecraft Config Editor (`/extensions/minecraftconfigeditor/servers/{serverIdentifier}` prefix)**
    *   `GET /`: Get Minecraft server configuration.
    *   `POST /save`: Save updated Minecraft configuration.
*   **Minecraft Player Manager (`/extensions/minecraftplayermanager/servers/{serverIdentifier}` prefix)**
    *   `GET /`: Get lists of players (online, whitelisted, banned, op).
    *   `POST /whitelist/status`: Enable or disable the whitelist.
    *   `PUT /whitelist`: Add a player to the whitelist.
    *   `DELETE /whitelist`: Remove a player from the whitelist.
    *   `PUT /op`: OP a player.
    *   `DELETE /op`: De-OP a player.
    *   `PUT /ban`: Ban a player.
    *   `DELETE /ban`: Unban a player.
    *   `POST /kick`: Kick a player.
*   **Pull Files (`/extensions/pullfiles/servers/{serverIdentifier}` prefix)**
    *   `POST /query`: Query a remote URL for file details before pulling.
    *   `POST /pull`: Pull files from a remote URL.
    *   `DELETE /pull/{id}`: Cancel a running pull task.
*   **Subdomain Manager (`/extensions/subdomainmanager/servers/{serverIdentifier}` prefix)**
    *   `GET /`: List assigned subdomains.
    *   `POST /`: Create a new subdomain.
    *   `DELETE /{subdomain}`: Delete a subdomain.
    *   `PATCH /{subdomain}`: Update a subdomain.
*   **Version Changer (`/extensions/versionchanger/servers/{serverIdentifier}` prefix)**
    *   `GET /installed`: Get the currently installed game version.
    *   `POST /install`: Install a new game version.
    *   `GET /types`: Get available game types (e.g., Paper, Forge).
    *   `GET /types/{type}`: Get versions for a specific type.
    *   `GET /types/{type}/{version}`: Get builds for a specific version.
*   **Database Import/Export (`/extensions/databaseimportexport/{serverIdentifier}/{database}` prefix)**
    *   `POST /export`: Export a database.
    *   `POST /import`: Import a database from an uploaded file.
    *   `POST /import/remote`: Import a database from a remote URL.
*   **Server Importer (`/extensions/serverimporter/servers/{serverIdentifier}` prefix)**
    *   `GET /profiles`: Get importer profiles.
    *   `POST /import`: Start a server import.
    *   `POST /test-credentials`: Test remote credentials for an import.

---

### Application API Endpoints (`/api/application`)

These are for global, administrative actions.

*   **Users**
    *   `GET /users`: List all users.
    *   `POST /users`: Create a user.
    *   `GET /users/{id}`: Get a specific user.
    *   `PATCH /users/{id}`: Update a user.
    *   `DELETE /users/{id}`: Delete a user.
*   **Servers**
    *   `GET /servers`: List all servers.
    *   `POST /servers`: Create a server.
    *   `GET /servers/{id}`: Get a specific server.
    *   `PATCH /servers/{id}/details`: Update server details.
    *   `PATCH /servers/{id}/build`: Update server build configuration.
    *   `POST /servers/{id}/suspend`: Suspend a server.
    *   `POST /servers/{id}/unsuspend`: Unsuspend a server.
    *   `POST /servers/{id}/reinstall`: Reinstall a server.
    *   `DELETE /servers/{id}`: Delete a server.
*   **Nodes & Locations**
    *   `GET /nodes`: List all nodes.
    *   `GET /locations`: List all locations.
*   **Nests & Eggs**
    *   `GET /nests`: List all nests.
    *   `GET /nests/{id}`: Get a specific nest.
    *   `GET /nests/{nestId}/eggs`: List eggs in a nest.
    *   `GET /nests/{nestId}/eggs/{id}`: Get a specific egg.
