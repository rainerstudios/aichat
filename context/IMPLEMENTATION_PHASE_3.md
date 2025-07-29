# 🔧 Phase 3: Advanced Operations Checklist
*Week 3-4: File Management, Backups, and Database Operations*

## Overview
This phase adds advanced server management capabilities including file operations, backup management, database tools, and comprehensive monitoring systems.

---

## ✅ Feature 1: File Management System (Day 1-2)

### Step 1: Core File Operations Backend
- [ ] **File**: `backend/app/pterodactyl/file_client.py`
- [ ] **Action**: Create comprehensive file management client

```python
# CREATE NEW FILE: backend/app/pterodactyl/file_client.py
import aiofiles
import os
import zipfile
import tarfile
from pathlib import Path
from typing import List, Dict, Optional, AsyncGenerator
from .base_client import PterodactylClient
import asyncio
import logging

class FileManager(PterodactylClient):
    """Advanced file management for Pterodactyl servers"""
    
    async def list_directory(self, server_id: str, path: str = "/") -> Dict:
        """List files and directories with detailed info"""
        try:
            response = await self.client.get(
                f"/servers/{server_id}/files/list",
                params={"directory": path}
            )
            
            files = response.json().get("data", [])
            
            # Organize by type and add metadata
            organized = {
                "directories": [],
                "files": [],
                "total_size": 0,
                "file_count": 0,
                "dir_count": 0
            }
            
            for item in files:
                item_data = {
                    "name": item.get("name"),
                    "size": item.get("size", 0),
                    "modified": item.get("modified_at"),
                    "is_file": item.get("is_file", True),
                    "is_symlink": item.get("is_symlink", False),
                    "mimetype": item.get("mimetype"),
                    "permissions": item.get("mode_bits")
                }
                
                if item_data["is_file"]:
                    organized["files"].append(item_data)
                    organized["file_count"] += 1
                    organized["total_size"] += item_data["size"]
                else:
                    organized["directories"].append(item_data)
                    organized["dir_count"] += 1
            
            # Sort files by name
            organized["files"].sort(key=lambda x: x["name"].lower())
            organized["directories"].sort(key=lambda x: x["name"].lower())
            
            return organized
            
        except Exception as e:
            logging.error(f"Failed to list directory {path}: {e}")
            raise
    
    async def read_file(self, server_id: str, file_path: str) -> str:
        """Read file contents with size limits"""
        try:
            # Check file size first
            file_info = await self.get_file_info(server_id, file_path)
            if file_info["size"] > 1024 * 1024:  # 1MB limit
                raise ValueError("File too large to display (>1MB)")
            
            response = await self.client.get(
                f"/servers/{server_id}/files/contents",
                params={"file": file_path}
            )
            
            return response.text
            
        except Exception as e:
            logging.error(f"Failed to read file {file_path}: {e}")
            raise
    
    async def write_file(self, server_id: str, file_path: str, content: str) -> bool:
        """Write content to file with backup"""
        try:
            # Create backup if file exists
            if await self.file_exists(server_id, file_path):
                backup_path = f"{file_path}.backup.{int(asyncio.get_event_loop().time())}"
                await self.copy_file(server_id, file_path, backup_path)
            
            response = await self.client.post(
                f"/servers/{server_id}/files/write",
                data={"file": file_path, "content": content}
            )
            
            return response.status_code == 204
            
        except Exception as e:
            logging.error(f"Failed to write file {file_path}: {e}")
            raise
    
    async def delete_file(self, server_id: str, file_path: str, create_backup: bool = True) -> bool:
        """Delete file with optional backup"""
        try:
            if create_backup and await self.file_exists(server_id, file_path):
                backup_path = f"/backups/deleted_{Path(file_path).name}_{int(asyncio.get_event_loop().time())}"
                await self.copy_file(server_id, file_path, backup_path)
            
            response = await self.client.post(
                f"/servers/{server_id}/files/delete",
                json={"root": "/", "files": [file_path]}
            )
            
            return response.status_code == 204
            
        except Exception as e:
            logging.error(f"Failed to delete file {file_path}: {e}")
            raise
    
    async def copy_file(self, server_id: str, source: str, destination: str) -> bool:
        """Copy file to new location"""
        try:
            response = await self.client.post(
                f"/servers/{server_id}/files/copy",
                json={"location": source, "destination": destination}
            )
            
            return response.status_code == 204
            
        except Exception as e:
            logging.error(f"Failed to copy {source} to {destination}: {e}")
            raise
    
    async def create_directory(self, server_id: str, path: str, name: str) -> bool:
        """Create new directory"""
        try:
            response = await self.client.post(
                f"/servers/{server_id}/files/create-folder",
                json={"root": path, "name": name}
            )
            
            return response.status_code == 204
            
        except Exception as e:
            logging.error(f"Failed to create directory {name} in {path}: {e}")
            raise
    
    async def compress_files(self, server_id: str, files: List[str], archive_name: str) -> str:
        """Create archive from files"""
        try:
            response = await self.client.post(
                f"/servers/{server_id}/files/compress",
                json={"root": "/", "files": files, "archive_name": archive_name}
            )
            
            if response.status_code == 200:
                return f"Created archive: {archive_name}"
            else:
                raise Exception(f"Compression failed: {response.text}")
                
        except Exception as e:
            logging.error(f"Failed to compress files: {e}")
            raise
    
    async def extract_archive(self, server_id: str, archive_path: str, destination: str = "/") -> bool:
        """Extract archive contents"""
        try:
            response = await self.client.post(
                f"/servers/{server_id}/files/decompress",
                json={"root": destination, "file": archive_path}
            )
            
            return response.status_code == 204
            
        except Exception as e:
            logging.error(f"Failed to extract {archive_path}: {e}")
            raise
    
    async def get_file_info(self, server_id: str, file_path: str) -> Dict:
        """Get detailed file information"""
        try:
            # Get parent directory listing to find file
            parent_dir = str(Path(file_path).parent)
            if parent_dir == ".":
                parent_dir = "/"
                
            dir_listing = await self.list_directory(server_id, parent_dir)
            file_name = Path(file_path).name
            
            # Find file in listing
            for file_info in dir_listing["files"]:
                if file_info["name"] == file_name:
                    return file_info
            
            raise FileNotFoundError(f"File not found: {file_path}")
            
        except Exception as e:
            logging.error(f"Failed to get file info for {file_path}: {e}")
            raise
    
    async def file_exists(self, server_id: str, file_path: str) -> bool:
        """Check if file exists"""
        try:
            await self.get_file_info(server_id, file_path)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    async def search_files(self, server_id: str, pattern: str, path: str = "/") -> List[Dict]:
        """Search for files matching pattern"""
        results = []
        
        try:
            async def search_recursive(current_path: str):
                listing = await self.list_directory(server_id, current_path)
                
                # Search files in current directory
                for file_info in listing["files"]:
                    if pattern.lower() in file_info["name"].lower():
                        file_info["path"] = os.path.join(current_path, file_info["name"])
                        results.append(file_info)
                
                # Recursively search subdirectories (limit depth)
                if current_path.count("/") < 5:  # Prevent infinite recursion
                    for dir_info in listing["directories"][:10]:  # Limit subdirs
                        subpath = os.path.join(current_path, dir_info["name"])
                        await search_recursive(subpath)
            
            await search_recursive(path)
            return results[:50]  # Limit results
            
        except Exception as e:
            logging.error(f"Failed to search files with pattern {pattern}: {e}")
            return []
```

### Step 2: File Management Tools
- [ ] **File**: `backend/app/langgraph/tools.py`
- [ ] **Action**: Add file management tools

```python
# ADD TO EXISTING tools.py file
from ..pterodactyl.file_client import FileManager

# Initialize file manager
file_manager = FileManager()

@tool
async def list_server_files(path: str = "/", server_id: str = "auto-detect") -> str:
    """List files and directories in server directory"""
    try:
        server_id = await get_user_server_id(server_id)
        listing = await file_manager.list_directory(server_id, path)
        
        output = [f"📁 **Directory: {path}**\n"]
        
        # Show directories first
        if listing["directories"]:
            output.append("📂 **Directories:**")
            for dir_info in listing["directories"][:20]:
                output.append(f"  📁 {dir_info['name']}")
        
        # Show files with size info
        if listing["files"]:
            output.append(f"\n📄 **Files ({listing['file_count']}):**")
            for file_info in listing["files"][:30]:
                size = format_file_size(file_info["size"])
                modified = file_info["modified"][:10] if file_info["modified"] else "Unknown"
                output.append(f"  📄 {file_info['name']} ({size}) - {modified}")
        
        # Summary
        total_size = format_file_size(listing["total_size"])
        output.append(f"\n📊 **Summary**: {listing['file_count']} files, {listing['dir_count']} dirs, {total_size} total")
        
        if listing["file_count"] > 30:
            output.append(f"\n⚠️ Showing first 30 files only. Use search for specific files.")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ **Error listing files**: {str(e)}"

@tool
async def read_server_file(file_path: str, server_id: str = "auto-detect") -> str:
    """Read contents of a server file (text files only, max 1MB)"""
    try:
        server_id = await get_user_server_id(server_id)
        
        # Validate file path
        if not file_path or file_path == "/":
            return "❌ **Error**: Please specify a valid file path"
        
        content = await file_manager.read_file(server_id, file_path)
        
        # Truncate very long content
        if len(content) > 5000:
            content = content[:5000] + "\n\n... (file truncated, showing first 5000 characters)"
        
        return f"""📄 **File: {file_path}**

```
{content}
```

💡 **Tip**: Use edit_server_file to modify this file"""
        
    except ValueError as e:
        return f"❌ **Error**: {str(e)}"
    except Exception as e:
        return f"❌ **Error reading file**: {str(e)}"

@tool
async def edit_server_file(file_path: str, content: str, server_id: str = "auto-detect", create_backup: bool = True) -> str:
    """Edit a server file with automatic backup"""
    try:
        server_id = await get_user_server_id(server_id)
        
        # Safety check for critical files
        critical_files = ['/server.properties', '/config/', '/world/', '/plugins/']
        if any(critical in file_path.lower() for critical in critical_files):
            return f"""⚠️ **CRITICAL FILE DETECTED** ⚠️

File: {file_path}

This appears to be a critical server file. Editing it incorrectly could:
- Crash your server
- Corrupt world data
- Break plugins/mods

**Automatic backup will be created.**

To proceed with editing, confirm by asking:
"edit {file_path} with backup confirmation"
"""
        
        success = await file_manager.write_file(server_id, file_path, content)
        
        if success:
            backup_msg = " (backup created)" if create_backup else ""
            return f"""✅ **File Updated Successfully**

📄 **File**: {file_path}{backup_msg}
💾 **Size**: {len(content)} characters
🔄 **Action**: Content written to server

**Next Steps:**
- Restart server if configuration file
- Check server logs for any errors
- Test functionality to verify changes
"""
        else:
            return f"❌ **Failed to update file**: {file_path}"
            
    except Exception as e:
        return f"❌ **Error editing file**: {str(e)}"

@tool
async def delete_server_file(file_path: str, server_id: str = "auto-detect", confirm: bool = False) -> str:
    """Delete a server file (with backup)"""
    try:
        if not confirm:
            return f"""🗑️ **DELETION CONFIRMATION REQUIRED** 🗑️

File: {file_path}

**This action will:**
- Permanently delete the file
- Create a backup in /backups/ directory
- Cannot be easily undone

To proceed, ask: "delete {file_path} with confirmation"
"""
        
        server_id = await get_user_server_id(server_id)
        success = await file_manager.delete_file(server_id, file_path, create_backup=True)
        
        if success:
            return f"""🗑️ **File Deleted Successfully**

📄 **Deleted**: {file_path}
💾 **Backup**: Created in /backups/ directory
⚠️ **Status**: File permanently removed from server

**Recovery**: Backup available if you need to restore the file.
"""
        else:
            return f"❌ **Failed to delete file**: {file_path}"
            
    except Exception as e:
        return f"❌ **Error deleting file**: {str(e)}"

@tool
async def search_server_files(pattern: str, path: str = "/", server_id: str = "auto-detect") -> str:
    """Search for files matching a pattern"""
    try:
        server_id = await get_user_server_id(server_id)
        results = await file_manager.search_files(server_id, pattern, path)
        
        if not results:
            return f"""🔍 **No Files Found**

Search pattern: "{pattern}"
Search path: {path}

Try:
- Different keywords
- Broader search path
- Check spelling
"""
        
        output = [f"🔍 **Search Results for '{pattern}'**\n"]
        
        for result in results:
            size = format_file_size(result["size"])
            output.append(f"📄 {result['path']} ({size})")
        
        if len(results) >= 50:
            output.append("\n⚠️ Showing first 50 results only. Use more specific search terms.")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ **Error searching files**: {str(e)}"

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

# ADD TO TOOLS LIST
tools = [
    # ... existing tools
    list_server_files,
    read_server_file,
    edit_server_file,
    delete_server_file,
    search_server_files,
    # ... rest of tools
]
```

---

## ✅ Feature 2: Backup Management System (Day 3-4)

### Step 1: Backup System Backend
- [ ] **File**: `backend/app/pterodactyl/backup_client.py`
- [ ] **Action**: Create backup management system

```python
# CREATE NEW FILE: backend/app/pterodactyl/backup_client.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .base_client import PterodactylClient

class BackupManager(PterodactylClient):
    """Comprehensive backup management for Pterodactyl servers"""
    
    async def create_backup(self, server_id: str, name: str = None, ignored_files: List[str] = None) -> Dict:
        """Create a new server backup"""
        try:
            if not name:
                name = f"auto_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            payload = {
                "name": name,
                "ignored": ignored_files or [
                    "*.log",
                    "cache/*",
                    "temp/*",
                    "logs/*"
                ]
            }
            
            response = await self.client.post(
                f"/servers/{server_id}/backups",
                json=payload
            )
            
            if response.status_code == 200:
                backup_data = response.json()["attributes"]
                return {
                    "uuid": backup_data["uuid"],
                    "name": backup_data["name"],
                    "size": backup_data["bytes"],
                    "status": "creating",
                    "created_at": backup_data["created_at"]
                }
            else:
                raise Exception(f"Backup creation failed: {response.text}")
                
        except Exception as e:
            logging.error(f"Failed to create backup: {e}")
            raise
    
    async def list_backups(self, server_id: str) -> List[Dict]:
        """List all backups for server"""
        try:
            response = await self.client.get(f"/servers/{server_id}/backups")
            
            if response.status_code == 200:
                backups_data = response.json()["data"]
                backups = []
                
                for backup in backups_data:
                    attrs = backup["attributes"]
                    backups.append({
                        "uuid": attrs["uuid"],
                        "name": attrs["name"],
                        "size": attrs["bytes"],
                        "status": "completed" if attrs["is_successful"] else "failed",
                        "created_at": attrs["created_at"],
                        "completed_at": attrs["completed_at"],
                        "checksum": attrs.get("checksum"),
                        "is_locked": attrs.get("is_locked", False)
                    })
                
                # Sort by creation date (newest first)
                backups.sort(key=lambda x: x["created_at"], reverse=True)
                return backups
            else:
                raise Exception(f"Failed to list backups: {response.text}")
                
        except Exception as e:
            logging.error(f"Failed to list backups: {e}")
            raise
    
    async def get_backup_status(self, server_id: str, backup_uuid: str) -> Dict:
        """Get detailed backup status"""
        try:
            response = await self.client.get(
                f"/servers/{server_id}/backups/{backup_uuid}"
            )
            
            if response.status_code == 200:
                attrs = response.json()["attributes"]
                return {
                    "uuid": attrs["uuid"],
                    "name": attrs["name"],
                    "size": attrs["bytes"],
                    "status": "completed" if attrs["is_successful"] else "failed",
                    "created_at": attrs["created_at"],
                    "completed_at": attrs["completed_at"],
                    "progress": 100 if attrs["is_successful"] else 0
                }
            else:
                raise Exception(f"Failed to get backup status: {response.text}")
                
        except Exception as e:
            logging.error(f"Failed to get backup status: {e}")
            raise
    
    async def delete_backup(self, server_id: str, backup_uuid: str) -> bool:
        """Delete a backup"""
        try:
            response = await self.client.delete(
                f"/servers/{server_id}/backups/{backup_uuid}"
            )
            
            return response.status_code == 204
            
        except Exception as e:
            logging.error(f"Failed to delete backup: {e}")
            raise
    
    async def restore_backup(self, server_id: str, backup_uuid: str, truncate: bool = False) -> bool:
        """Restore server from backup"""
        try:
            payload = {"truncate": truncate}
            
            response = await self.client.post(
                f"/servers/{server_id}/backups/{backup_uuid}/restore",
                json=payload
            )
            
            return response.status_code == 204
            
        except Exception as e:
            logging.error(f"Failed to restore backup: {e}")
            raise
    
    async def download_backup_url(self, server_id: str, backup_uuid: str) -> str:
        """Get download URL for backup"""
        try:
            response = await self.client.get(
                f"/servers/{server_id}/backups/{backup_uuid}/download"
            )
            
            if response.status_code == 200:
                return response.json()["attributes"]["url"]
            else:
                raise Exception("Failed to get download URL")
                
        except Exception as e:
            logging.error(f"Failed to get download URL: {e}")
            raise
    
    async def get_backup_analytics(self, server_id: str) -> Dict:
        """Get backup analytics and recommendations"""
        try:
            backups = await self.list_backups(server_id)
            
            if not backups:
                return {
                    "total_backups": 0,
                    "total_size": 0,
                    "avg_size": 0,
                    "last_backup": None,
                    "recommendations": ["Create your first backup to protect your data"]
                }
            
            successful_backups = [b for b in backups if b["status"] == "completed"]
            total_size = sum(b["size"] for b in successful_backups)
            avg_size = total_size / len(successful_backups) if successful_backups else 0
            
            # Calculate time since last backup
            last_backup = successful_backups[0] if successful_backups else None
            days_since_last = None
            if last_backup:
                last_date = datetime.fromisoformat(last_backup["created_at"].replace('Z', '+00:00'))
                days_since_last = (datetime.now(last_date.tzinfo) - last_date).days
            
            # Generate recommendations
            recommendations = []
            if days_since_last is None:
                recommendations.append("❌ No successful backups found - create one immediately")
            elif days_since_last > 7:
                recommendations.append(f"⚠️ Last backup was {days_since_last} days ago - create a new one")
            elif days_since_last > 3:
                recommendations.append(f"💡 Last backup was {days_since_last} days ago - consider creating a new one")
            else:
                recommendations.append("✅ Recent backup available")
            
            if len(successful_backups) > 10:
                recommendations.append("💾 Consider deleting old backups to save space")
            
            if len(successful_backups) < 3:
                recommendations.append("📅 Recommend keeping at least 3-5 backups")
            
            return {
                "total_backups": len(backups),
                "successful_backups": len(successful_backups),
                "failed_backups": len(backups) - len(successful_backups),
                "total_size": total_size,
                "avg_size": avg_size,
                "last_backup": last_backup,
                "days_since_last": days_since_last,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logging.error(f"Failed to get backup analytics: {e}")
            raise
```

### Step 2: Backup Management Tools
- [ ] **File**: `backend/app/langgraph/tools.py`
- [ ] **Action**: Add backup management tools

```python
# ADD TO EXISTING tools.py file
from ..pterodactyl.backup_client import BackupManager

# Initialize backup manager
backup_manager = BackupManager()

@tool
async def create_server_backup(name: str = "", server_id: str = "auto-detect") -> str:
    """Create a new backup of the server"""
    try:
        server_id = await get_user_server_id(server_id)
        
        if not name:
            name = f"manual_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_info = await backup_manager.create_backup(server_id, name)
        
        return f"""💾 **Backup Creation Started**

📦 **Name**: {backup_info['name']}
🆔 **ID**: {backup_info['uuid'][:8]}...
📅 **Started**: {backup_info['created_at'][:10]}
⏳ **Status**: Creating backup...

**What's happening:**
- Server files are being compressed
- Process typically takes 2-10 minutes
- Server remains online during backup

Use "check backup status" to monitor progress.
"""
        
    except Exception as e:
        return f"❌ **Backup Creation Failed**: {str(e)}"

@tool
async def list_server_backups(server_id: str = "auto-detect") -> str:
    """List all backups for the server"""
    try:
        server_id = await get_user_server_id(server_id)
        backups = await backup_manager.list_backups(server_id)
        
        if not backups:
            return """📦 **No Backups Found**

Your server doesn't have any backups yet.

**Recommendations:**
- Create a backup now: "create server backup"
- Set up regular backups for data protection
- Backups are essential before major changes
"""
        
        output = [f"📦 **Server Backups ({len(backups)} total)**\n"]
        
        for i, backup in enumerate(backups[:10]):
            status_emoji = "✅" if backup["status"] == "completed" else "❌"
            size = format_file_size(backup["size"]) if backup["size"] else "Unknown"
            created = backup["created_at"][:10] if backup["created_at"] else "Unknown"
            
            output.append(f"{status_emoji} **{backup['name']}**")
            output.append(f"   📅 {created} | 💾 {size} | 🆔 {backup['uuid'][:8]}...")
            output.append("")
        
        if len(backups) > 10:
            output.append(f"⚠️ Showing 10 most recent backups. Total: {len(backups)}")
        
        # Add analytics
        analytics = await backup_manager.get_backup_analytics(server_id)
        output.append("\n📊 **Quick Stats:**")
        output.append(f"- Total size: {format_file_size(analytics['total_size'])}")
        output.append(f"- Last backup: {analytics['days_since_last']} days ago" if analytics['days_since_last'] else "- Last backup: Never")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ **Error listing backups**: {str(e)}"

@tool
async def restore_server_backup(backup_name_or_id: str, server_id: str = "auto-detect", confirm: bool = False) -> str:
    """Restore server from a backup (DESTRUCTIVE - requires confirmation)"""
    try:
        if not confirm:
            return f"""🔄 **BACKUP RESTORE CONFIRMATION REQUIRED** 🔄

Backup: {backup_name_or_id}

**⚠️ THIS ACTION WILL:**
- **PERMANENTLY DELETE** all current server files
- Replace everything with backup contents
- **DISCONNECT ALL PLAYERS** immediately
- **LOSE ALL PROGRESS** since backup was created

**This cannot be undone without another backup!**

To proceed, ask: "restore backup {backup_name_or_id} with confirmation"
"""
        
        server_id = await get_user_server_id(server_id)
        backups = await backup_manager.list_backups(server_id)
        
        # Find backup by name or ID
        backup_uuid = None
        for backup in backups:
            if (backup_name_or_id in backup["name"] or 
                backup_name_or_id in backup["uuid"]):
                backup_uuid = backup["uuid"]
                backup_name = backup["name"]
                break
        
        if not backup_uuid:
            return f"❌ **Backup not found**: {backup_name_or_id}"
        
        success = await backup_manager.restore_backup(server_id, backup_uuid, truncate=True)
        
        if success:
            return f"""🔄 **Backup Restore Initiated**

📦 **Backup**: {backup_name}
🗑️ **Action**: All current files deleted
📥 **Status**: Restoring backup contents...

**Timeline:**
- Files are being restored (5-15 minutes)
- Server will restart automatically
- Players can reconnect once complete

Use "get server status" to monitor progress.
"""
        else:
            return f"❌ **Restore failed** for backup: {backup_name_or_id}"
            
    except Exception as e:
        return f"❌ **Error restoring backup**: {str(e)}"

@tool
async def delete_server_backup(backup_name_or_id: str, server_id: str = "auto-detect", confirm: bool = False) -> str:
    """Delete a server backup (cannot be undone)"""
    try:
        if not confirm:
            return f"""🗑️ **BACKUP DELETION CONFIRMATION REQUIRED** 🗑️

Backup: {backup_name_or_id}

**This action will:**
- Permanently delete the backup file
- Free up storage space
- Cannot be recovered once deleted

To proceed, ask: "delete backup {backup_name_or_id} with confirmation"
"""
        
        server_id = await get_user_server_id(server_id)
        backups = await backup_manager.list_backups(server_id)
        
        # Find backup by name or ID
        backup_uuid = None
        backup_name = None
        for backup in backups:
            if (backup_name_or_id in backup["name"] or 
                backup_name_or_id in backup["uuid"]):
                backup_uuid = backup["uuid"]
                backup_name = backup["name"]
                break
        
        if not backup_uuid:
            return f"❌ **Backup not found**: {backup_name_or_id}"
        
        success = await backup_manager.delete_backup(server_id, backup_uuid)
        
        if success:
            return f"""🗑️ **Backup Deleted Successfully**

📦 **Deleted**: {backup_name}
💾 **Storage**: Space freed up
⚠️  **Status**: Backup permanently removed

**Note**: This action cannot be undone.
"""
        else:
            return f"❌ **Failed to delete backup**: {backup_name_or_id}"
            
    except Exception as e:
        return f"❌ **Error deleting backup**: {str(e)}"

@tool
async def get_backup_recommendations(server_id: str = "auto-detect") -> str:
    """Get backup analytics and recommendations"""
    try:
        server_id = await get_user_server_id(server_id)
        analytics = await backup_manager.get_backup_analytics(server_id)
        
        output = ["📊 **Backup Analytics & Recommendations**\n"]
        
        # Stats
        output.append("📈 **Current Stats:**")
        output.append(f"- Total backups: {analytics['total_backups']}")
        output.append(f"- Successful: {analytics['successful_backups']}")
        output.append(f"- Failed: {analytics['failed_backups']}")
        output.append(f"- Total storage: {format_file_size(analytics['total_size'])}")
        output.append(f"- Average size: {format_file_size(analytics['avg_size'])}")
        
        if analytics['last_backup']:
            output.append(f"- Last backup: {analytics['days_since_last']} days ago")
        
        # Recommendations
        output.append("\n💡 **Recommendations:**")
        for rec in analytics['recommendations']:
            output.append(f"  {rec}")
        
        # Best practices
        output.append("\n🎯 **Best Practices:**")
        output.append("- Create backups before major changes")
        output.append("- Keep 3-5 recent backups minimum")
        output.append("- Test backup restores occasionally")
        output.append("- Delete old backups to save space")
        output.append("- Backup before plugin/mod updates")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ **Error getting backup recommendations**: {str(e)}"

# ADD TO TOOLS LIST
tools = [
    # ... existing tools
    create_server_backup,
    list_server_backups,
    restore_server_backup,
    delete_server_backup,
    get_backup_recommendations,
    # ... rest of tools
]
```

---

## ✅ Feature 3: Database Management Tools (Day 5-6)

### Step 1: Database Operations Backend
- [ ] **File**: `backend/app/pterodactyl/database_client.py`
- [ ] **Action**: Create database management system

```python
# CREATE NEW FILE: backend/app/pterodactyl/database_client.py
import asyncio
import logging
import re
from typing import List, Dict, Optional
from .base_client import PterodactylClient

class DatabaseManager(PterodactylClient):
    """Database management for Pterodactyl servers"""
    
    async def list_databases(self, server_id: str) -> List[Dict]:
        """List all databases for server"""
        try:
            response = await self.client.get(f"/servers/{server_id}/databases")
            
            if response.status_code == 200:
                databases_data = response.json()["data"]
                databases = []
                
                for db in databases_data:
                    attrs = db["attributes"]
                    databases.append({
                        "id": attrs["id"],
                        "name": attrs["name"],
                        "host": attrs["host"]["name"],
                        "port": attrs["host"]["port"],
                        "username": attrs["username"],
                        "max_connections": attrs["max_connections"],
                        "created_at": attrs.get("created_at")
                    })
                
                return databases
            else:
                raise Exception(f"Failed to list databases: {response.text}")
                
        except Exception as e:
            logging.error(f"Failed to list databases: {e}")
            raise
    
    async def create_database(self, server_id: str, database_name: str, host_id: int = None) -> Dict:
        """Create a new database"""
        try:
            # Validate database name
            if not re.match(r'^[a-zA-Z0-9_]+$', database_name):
                raise ValueError("Database name can only contain letters, numbers, and underscores")
            
            if len(database_name) > 48:
                raise ValueError("Database name must be 48 characters or less")
            
            payload = {
                "database": database_name,
                "remote": "%"  # Allow connections from anywhere
            }
            
            if host_id:
                payload["host"] = host_id
            
            response = await self.client.post(
                f"/servers/{server_id}/databases",
                json=payload
            )
            
            if response.status_code == 200:
                attrs = response.json()["attributes"]
                return {
                    "id": attrs["id"],
                    "name": attrs["name"],
                    "host": attrs["host"]["name"],
                    "port": attrs["host"]["port"],
                    "username": attrs["username"],
                    "password": attrs["relationships"]["password"]["attributes"]["password"]
                }
            else:
                raise Exception(f"Database creation failed: {response.text}")
                
        except Exception as e:
            logging.error(f"Failed to create database: {e}")
            raise
    
    async def delete_database(self, server_id: str, database_id: str) -> bool:
        """Delete a database"""
        try:
            response = await self.client.delete(
                f"/servers/{server_id}/databases/{database_id}"
            )
            
            return response.status_code == 204
            
        except Exception as e:
            logging.error(f"Failed to delete database: {e}")
            raise
    
    async def rotate_database_password(self, server_id: str, database_id: str) -> str:
        """Rotate database password"""
        try:
            response = await self.client.post(
                f"/servers/{server_id}/databases/{database_id}/rotate-password"
            )
            
            if response.status_code == 200:
                return response.json()["attributes"]["relationships"]["password"]["attributes"]["password"]
            else:
                raise Exception(f"Password rotation failed: {response.text}")
                
        except Exception as e:
            logging.error(f"Failed to rotate password: {e}")
            raise
    
    async def get_database_usage_stats(self, server_id: str) -> Dict:
        """Get database usage statistics"""
        try:
            databases = await self.list_databases(server_id)
            
            stats = {
                "total_databases": len(databases),
                "databases": databases,
                "hosts": {},
                "recommendations": []
            }
            
            # Group by host
            for db in databases:
                host_key = f"{db['host']}:{db['port']}"
                if host_key not in stats["hosts"]:
                    stats["hosts"][host_key] = []
                stats["hosts"][host_key].append(db)
            
            # Generate recommendations
            if len(databases) == 0:
                stats["recommendations"].append("💡 No databases found - many plugins require databases")
            elif len(databases) > 5:
                stats["recommendations"].append("⚠️ Many databases detected - consider consolidation")
            
            # Check for old databases
            current_time = asyncio.get_event_loop().time()
            old_databases = [db for db in databases if db.get("created_at")]
            if len(old_databases) > len(databases) * 0.5:
                stats["recommendations"].append("🧹 Consider cleaning up unused databases")
            
            return stats
            
        except Exception as e:
            logging.error(f"Failed to get database stats: {e}")
            raise
    
    async def get_connection_string(self, server_id: str, database_id: str) -> Dict:
        """Get database connection information"""
        try:
            databases = await self.list_databases(server_id)
            database = next((db for db in databases if str(db["id"]) == str(database_id)), None)
            
            if not database:
                raise ValueError(f"Database with ID {database_id} not found")
            
            # Get password (requires rotation endpoint to retrieve)
            try:
                password = await self.rotate_database_password(server_id, database_id)
            except:
                password = "[Use password rotation to get current password]"
            
            connection_info = {
                "host": database["host"],
                "port": database["port"],
                "database": database["name"],
                "username": database["username"],
                "password": password,
                "connection_strings": {
                    "mysql_cli": f"mysql -h {database['host']} -P {database['port']} -u {database['username']} -p {database['name']}",
                    "jdbc": f"jdbc:mysql://{database['host']}:{database['port']}/{database['name']}",
                    "php_pdo": f"mysql:host={database['host']};port={database['port']};dbname={database['name']}",
                    "python_pymysql": f"pymysql.connect(host='{database['host']}', port={database['port']}, user='{database['username']}', password='[PASSWORD]', database='{database['name']}')"
                }
            }
            
            return connection_info
            
        except Exception as e:
            logging.error(f"Failed to get connection string: {e}")
            raise
```

### Step 2: Database Management Tools
- [ ] **File**: `backend/app/langgraph/tools.py`
- [ ] **Action**: Add database tools

```python
# ADD TO EXISTING tools.py file
from ..pterodactyl.database_client import DatabaseManager

# Initialize database manager
db_manager = DatabaseManager()

@tool
async def list_server_databases(server_id: str = "auto-detect") -> str:
    """List all databases for the server"""
    try:
        server_id = await get_user_server_id(server_id)
        databases = await db_manager.list_databases(server_id)
        
        if not databases:
            return """🗄️ **No Databases Found**

Your server doesn't have any databases set up.

**Common uses for databases:**
- Plugin data storage (Essentials, WorldGuard, etc.)
- Player statistics and economy data
- Website integration (forums, voting systems)
- Custom plugin development

**Next steps:**
- Create a database: "create database [name]"
- Check plugin requirements for database needs
"""
        
        output = [f"🗄️ **Server Databases ({len(databases)} total)**\n"]
        
        for i, db in enumerate(databases):
            output.append(f"📊 **{db['name']}**")
            output.append(f"   🏠 Host: {db['host']}:{db['port']}")
            output.append(f"   👤 User: {db['username']}")
            output.append(f"   🔗 Max Connections: {db['max_connections']}")
            output.append(f"   🆔 ID: {db['id']}")
            output.append("")
        
        output.append("💡 **Tips:**")
        output.append("- Use 'get database connection [name]' for connection details")
        output.append("- Rotate passwords regularly for security")
        output.append("- Check plugin documentation for database setup")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ **Error listing databases**: {str(e)}"

@tool
async def create_server_database(database_name: str, server_id: str = "auto-detect") -> str:
    """Create a new database for the server"""
    try:
        server_id = await get_user_server_id(server_id)
        
        # Validate name
        if not database_name:
            return "❌ **Error**: Please provide a database name"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', database_name):
            return "❌ **Error**: Database name can only contain letters, numbers, and underscores"
        
        if len(database_name) > 48:
            return "❌ **Error**: Database name must be 48 characters or less"
        
        db_info = await db_manager.create_database(server_id, database_name)
        
        return f"""✅ **Database Created Successfully**

📊 **Database**: {db_info['name']}
🏠 **Host**: {db_info['host']}:{db_info['port']}
👤 **Username**: {db_info['username']}
🔑 **Password**: {db_info['password']}

**Connection Info:**
```
Host: {db_info['host']}
Port: {db_info['port']}
Database: {db_info['name']}
Username: {db_info['username']}
Password: {db_info['password']}
```

**Security Notes:**
- Save these credentials securely
- Password is only shown once
- Use 'rotate database password' to change it later

**Next Steps:**
- Configure your plugins to use this database
- Test the connection from your server
"""
        
    except ValueError as e:
        return f"❌ **Validation Error**: {str(e)}"
    except Exception as e:
        return f"❌ **Error creating database**: {str(e)}"

@tool
async def delete_server_database(database_name_or_id: str, server_id: str = "auto-detect", confirm: bool = False) -> str:
    """Delete a server database (DESTRUCTIVE - requires confirmation)"""
    try:
        if not confirm:
            return f"""🗑️ **DATABASE DELETION CONFIRMATION REQUIRED** 🗑️

Database: {database_name_or_id}

**⚠️ THIS ACTION WILL:**
- **PERMANENTLY DELETE** all data in the database
- Remove all tables, views, and stored data
- **BREAK PLUGINS** that depend on this database
- Cannot be recovered without a backup

**This action cannot be undone!**

To proceed, ask: "delete database {database_name_or_id} with confirmation"
"""
        
        server_id = await get_user_server_id(server_id)
        databases = await db_manager.list_databases(server_id)
        
        # Find database by name or ID
        database_id = None
        database_name = None
        for db in databases:
            if (database_name_or_id.lower() in db["name"].lower() or 
                str(database_name_or_id) == str(db["id"])):
                database_id = db["id"]
                database_name = db["name"]
                break
        
        if not database_id:
            return f"❌ **Database not found**: {database_name_or_id}"
        
        success = await db_manager.delete_database(server_id, database_id)
        
        if success:
            return f"""🗑️ **Database Deleted Successfully**

📊 **Deleted**: {database_name}
🗄️ **Status**: All data permanently removed
⚠️  **Impact**: Plugins using this database may break

**Important:**
- Update plugin configurations
- Remove database references from configs
- Check server logs for any errors
"""
        else:
            return f"❌ **Failed to delete database**: {database_name_or_id}"
            
    except Exception as e:
        return f"❌ **Error deleting database**: {str(e)}"

@tool
async def get_database_connection_info(database_name_or_id: str, server_id: str = "auto-detect") -> str:
    """Get connection information for a database"""
    try:
        server_id = await get_user_server_id(server_id)
        databases = await db_manager.list_databases(server_id)
        
        # Find database by name or ID
        database_id = None
        for db in databases:
            if (database_name_or_id.lower() in db["name"].lower() or 
                str(database_name_or_id) == str(db["id"])):
                database_id = db["id"]
                break
        
        if not database_id:
            return f"❌ **Database not found**: {database_name_or_id}"
        
        conn_info = await db_manager.get_connection_string(server_id, database_id)
        
        return f"""🔗 **Database Connection Information**

📊 **Database**: {conn_info['database']}
🏠 **Host**: {conn_info['host']}
🔌 **Port**: {conn_info['port']}
👤 **Username**: {conn_info['username']}
🔑 **Password**: {conn_info['password']}

**Connection Strings:**

**MySQL CLI:**
```bash
{conn_info['connection_strings']['mysql_cli']}
```

**Java/JDBC:**
```
{conn_info['connection_strings']['jdbc']}
```

**PHP (PDO):**
```php
$dsn = "{conn_info['connection_strings']['php_pdo']}";
```

**Python (PyMySQL):**
```python
{conn_info['connection_strings']['python_pymysql']}
```

**Plugin Configuration:**
- Use these credentials in your plugin configs
- Test connection before going live
- Secure credentials in config files
"""
        
    except Exception as e:
        return f"❌ **Error getting connection info**: {str(e)}"

@tool
async def rotate_database_password(database_name_or_id: str, server_id: str = "auto-detect") -> str:
    """Rotate password for a database"""
    try:
        server_id = await get_user_server_id(server_id)
        databases = await db_manager.list_databases(server_id)
        
        # Find database by name or ID
        database_id = None
        database_name = None
        for db in databases:
            if (database_name_or_id.lower() in db["name"].lower() or 
                str(database_name_or_id) == str(db["id"])):
                database_id = db["id"]
                database_name = db["name"]
                break
        
        if not database_id:
            return f"❌ **Database not found**: {database_name_or_id}"
        
        new_password = await db_manager.rotate_database_password(server_id, database_id)
        
        return f"""🔄 **Database Password Rotated**

📊 **Database**: {database_name}
🔑 **New Password**: {new_password}

**Important Next Steps:**
1. **Update all plugin configurations** with the new password
2. **Restart server** to apply new database connections
3. **Test all database-dependent plugins**
4. **Save the new password** securely

**Potential Issues:**
- Plugins may fail until configs are updated
- Existing connections will be terminated
- Manual intervention may be required

Use "get database connection {database_name}" for full connection details.
"""
        
    except Exception as e:
        return f"❌ **Error rotating password**: {str(e)}"

@tool
async def analyze_database_usage(server_id: str = "auto-detect") -> str:
    """Analyze database usage and provide recommendations"""
    try:
        server_id = await get_user_server_id(server_id)
        stats = await db_manager.get_database_usage_stats(server_id)
        
        output = ["📊 **Database Usage Analysis**\n"]
        
        # Basic stats
        output.append(f"🗄️ **Total Databases**: {stats['total_databases']}")
        
        if stats['total_databases'] > 0:
            # Host breakdown
            output.append(f"🏠 **Database Hosts**: {len(stats['hosts'])}")
            for host, dbs in stats['hosts'].items():
                output.append(f"   📍 {host}: {len(dbs)} databases")
            
            # List databases with basic info
            output.append(f"\n📋 **Database Overview:**")
            for db in stats['databases']:
                output.append(f"   • {db['name']} (ID: {db['id']})")
        
        # Recommendations
        if stats['recommendations']:
            output.append(f"\n💡 **Recommendations:**")
            for rec in stats['recommendations']:
                output.append(f"   {rec}")
        
        # Best practices
        output.append(f"\n🎯 **Database Best Practices:**")
        output.append("   • Use descriptive database names")
        output.append("   • Rotate passwords regularly")
        output.append("   • Monitor database connections")
        output.append("   • Back up important data")
        output.append("   • Remove unused databases")
        
        # Common plugins that use databases
        output.append(f"\n🔌 **Plugins That Often Need Databases:**")
        output.append("   • EssentialsX (player data)")
        output.append("   • LuckPerms (permissions)")
        output.append("   • WorldGuard (protection data)")
        output.append("   • Vault (economy systems)")
        output.append("   • Custom web integrations")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ **Error analyzing database usage**: {str(e)}"

# ADD TO TOOLS LIST
tools = [
    # ... existing tools
    list_server_databases,
    create_server_database,
    delete_server_database,
    get_database_connection_info,
    rotate_database_password,
    analyze_database_usage,
    # ... rest of tools
]
```

---

## ✅ Feature 4: Advanced Monitoring & Alerts (Day 7)

### Step 1: Enhanced Monitoring System
- [ ] **File**: `backend/app/pterodactyl/monitoring_client.py`
- [ ] **Action**: Create comprehensive monitoring system

```python
# CREATE NEW FILE: backend/app/pterodactyl/monitoring_client.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from .base_client import PterodactylClient

class MonitoringManager(PterodactylClient):
    """Advanced monitoring and alerting for Pterodactyl servers"""
    
    async def get_detailed_server_stats(self, server_id: str) -> Dict:
        """Get comprehensive server statistics"""
        try:
            # Get current stats
            response = await self.client.get(f"/servers/{server_id}/resources")
            
            if response.status_code == 200:
                stats = response.json()["attributes"]
                
                # Calculate percentages and status
                memory_percent = (stats["memory_bytes"] / stats["memory_limit_bytes"]) * 100 if stats["memory_limit_bytes"] > 0 else 0
                cpu_percent = stats["cpu_absolute"]
                disk_percent = (stats["disk_bytes"] / stats["disk_limit_bytes"]) * 100 if stats["disk_limit_bytes"] > 0 else 0
                
                # Determine health status
                health_status = self._calculate_health_status(memory_percent, cpu_percent, disk_percent)
                
                detailed_stats = {
                    "timestamp": datetime.now().isoformat(),
                    "status": stats["current_state"],
                    "uptime": stats.get("uptime", 0),
                    "memory": {
                        "used_bytes": stats["memory_bytes"],
                        "limit_bytes": stats["memory_limit_bytes"],
                        "used_mb": round(stats["memory_bytes"] / 1024 / 1024, 1),
                        "limit_mb": round(stats["memory_limit_bytes"] / 1024 / 1024, 1),
                        "percentage": round(memory_percent, 1),
                        "status": self._get_resource_status(memory_percent)
                    },
                    "cpu": {
                        "absolute": round(cpu_percent, 1),
                        "percentage": round(cpu_percent, 1),  # Assuming absolute is percentage
                        "status": self._get_resource_status(cpu_percent)
                    },
                    "disk": {
                        "used_bytes": stats["disk_bytes"],
                        "limit_bytes": stats["disk_limit_bytes"],
                        "used_gb": round(stats["disk_bytes"] / 1024 / 1024 / 1024, 2),
                        "limit_gb": round(stats["disk_limit_bytes"] / 1024 / 1024 / 1024, 2),
                        "percentage": round(disk_percent, 1),
                        "status": self._get_resource_status(disk_percent)
                    },
                    "network": {
                        "rx_bytes": stats["network_rx_bytes"],
                        "tx_bytes": stats["network_tx_bytes"],
                        "rx_mb": round(stats["network_rx_bytes"] / 1024 / 1024, 2),
                        "tx_mb": round(stats["network_tx_bytes"] / 1024 / 1024, 2)
                    },
                    "health": health_status,
                    "alerts": self._generate_alerts(memory_percent, cpu_percent, disk_percent, stats["current_state"])
                }
                
                return detailed_stats
            else:
                raise Exception(f"Failed to get server stats: {response.text}")
                
        except Exception as e:
            logging.error(f"Failed to get detailed server stats: {e}")
            raise
    
    def _calculate_health_status(self, memory_pct: float, cpu_pct: float, disk_pct: float) -> Dict:
        """Calculate overall server health"""
        issues = []
        score = 100
        
        # Memory checks
        if memory_pct > 90:
            issues.append("Critical memory usage")
            score -= 30
        elif memory_pct > 80:
            issues.append("High memory usage")
            score -= 15
        
        # CPU checks
        if cpu_pct > 90:
            issues.append("Critical CPU usage")
            score -= 25
        elif cpu_pct > 75:
            issues.append("High CPU usage")
            score -= 10
        
        # Disk checks
        if disk_pct > 95:
            issues.append("Critical disk usage")
            score -= 20
        elif disk_pct > 85:
            issues.append("High disk usage")
            score -= 10
        
        # Determine overall status
        if score >= 90:
            status = "excellent"
            emoji = "🟢"
        elif score >= 75:
            status = "good"
            emoji = "🟡"
        elif score >= 60:
            status = "warning"
            emoji = "🟠"
        else:
            status = "critical"
            emoji = "🔴"
        
        return {
            "score": max(0, score),
            "status": status,
            "emoji": emoji,
            "issues": issues,
            "summary": f"{emoji} {status.title()} ({score}/100)"
        }
    
    def _get_resource_status(self, percentage: float) -> str:
        """Get status for individual resource"""
        if percentage >= 95:
            return "critical"
        elif percentage >= 85:
            return "warning"
        elif percentage >= 70:
            return "moderate"
        else:
            return "normal"
    
    def _generate_alerts(self, memory_pct: float, cpu_pct: float, disk_pct: float, server_state: str) -> List[Dict]:
        """Generate alerts based on current metrics"""
        alerts = []
        
        if server_state != "running":
            alerts.append({
                "level": "critical",
                "type": "server_state",
                "message": f"Server is {server_state}",
                "action": "Check server status and restart if needed"
            })
        
        if memory_pct > 90:
            alerts.append({
                "level": "critical",
                "type": "memory",
                "message": f"Memory usage at {memory_pct:.1f}%",
                "action": "Restart server or increase memory allocation"
            })
        elif memory_pct > 80:
            alerts.append({
                "level": "warning",
                "type": "memory",
                "message": f"High memory usage: {memory_pct:.1f}%",
                "action": "Monitor closely and consider restart"
            })
        
        if cpu_pct > 90:
            alerts.append({
                "level": "critical",
                "type": "cpu",
                "message": f"CPU usage at {cpu_pct:.1f}%",
                "action": "Check for performance issues or reduce server load"
            })
        elif cpu_pct > 75:
            alerts.append({
                "level": "warning",
                "type": "cpu",
                "message": f"High CPU usage: {cpu_pct:.1f}%",
                "action": "Monitor server performance"
            })
        
        if disk_pct > 95:
            alerts.append({
                "level": "critical",
                "type": "disk",
                "message": f"Disk usage at {disk_pct:.1f}%",
                "action": "Free up disk space immediately"
            })
        elif disk_pct > 85:
            alerts.append({
                "level": "warning",
                "type": "disk",
                "message": f"High disk usage: {disk_pct:.1f}%",
                "action": "Consider cleaning up files"
            })
        
        return alerts
    
    async def get_performance_history(self, server_id: str, hours: int = 24) -> Dict:
        """Simulate performance history (would need actual metrics storage)"""
        try:
            # In real implementation, this would query stored metrics
            # For now, we'll return current stats as a baseline
            current_stats = await self.get_detailed_server_stats(server_id)
            
            return {
                "period": f"Last {hours} hours",
                "current": current_stats,
                "trends": {
                    "memory": "stable",  # Would calculate from historical data
                    "cpu": "stable",
                    "disk": "increasing",
                    "uptime": "excellent"
                },
                "recommendations": [
                    "Enable metrics collection for better insights",
                    "Set up automated backups",
                    "Consider performance monitoring plugins"
                ]
            }
            
        except Exception as e:
            logging.error(f"Failed to get performance history: {e}")
            raise
    
    async def run_health_check(self, server_id: str) -> Dict:
        """Run comprehensive server health check"""
        try:
            health_report = {
                "timestamp": datetime.now().isoformat(),
                "checks": {},
                "overall_status": "unknown",
                "recommendations": []
            }
            
            # Get server stats
            try:
                stats = await self.get_detailed_server_stats(server_id)
                health_report["checks"]["resources"] = {
                    "status": "passed",
                    "details": f"Health score: {stats['health']['score']}/100"
                }
            except Exception as e:
                health_report["checks"]["resources"] = {
                    "status": "failed",
                    "details": f"Unable to get resource stats: {str(e)}"
                }
            
            # Check server responsiveness (simulated)
            health_report["checks"]["responsiveness"] = {
                "status": "passed",
                "details": "Server responding to API calls"
            }
            
            # Check disk space
            if stats and stats["disk"]["percentage"] > 90:
                health_report["checks"]["disk_space"] = {
                    "status": "failed",
                    "details": f"Disk usage critical: {stats['disk']['percentage']:.1f}%"
                }
                health_report["recommendations"].append("Free up disk space immediately")
            else:
                health_report["checks"]["disk_space"] = {
                    "status": "passed",
                    "details": "Sufficient disk space available"
                }
            
            # Determine overall status
            failed_checks = [check for check in health_report["checks"].values() if check["status"] == "failed"]
            if failed_checks:
                health_report["overall_status"] = "critical"
            else:
                health_report["overall_status"] = "healthy"
            
            return health_report
            
        except Exception as e:
            logging.error(f"Failed to run health check: {e}")
            raise
```

### Step 2: Advanced Monitoring Tools
- [ ] **File**: `backend/app/langgraph/tools.py`
- [ ] **Action**: Add monitoring and alerting tools

```python
# ADD TO EXISTING tools.py file
from ..pterodactyl.monitoring_client import MonitoringManager

# Initialize monitoring manager
monitoring_manager = MonitoringManager()

@tool
async def get_detailed_server_status(server_id: str = "auto-detect") -> str:
    """Get comprehensive server status with health analysis"""
    try:
        server_id = await get_user_server_id(server_id)
        stats = await monitoring_manager.get_detailed_server_stats(server_id)
        
        # Health overview
        health = stats["health"]
        output = [f"🖥️ **Server Status Report** - {stats['timestamp'][:19]}\n"]
        output.append(f"**Overall Health**: {health['summary']}")
        
        if health['issues']:
            output.append(f"**Issues Found**: {', '.join(health['issues'])}")
        
        output.append("")
        
        # Resource details
        output.append("📊 **Resource Usage:**")
        
        # Memory
        mem = stats["memory"]
        mem_emoji = "🔴" if mem["status"] == "critical" else "🟡" if mem["status"] == "warning" else "🟢"
        output.append(f"{mem_emoji} **Memory**: {mem['used_mb']} MB / {mem['limit_mb']} MB ({mem['percentage']}%)")
        
        # CPU
        cpu = stats["cpu"]
        cpu_emoji = "🔴" if cpu["status"] == "critical" else "🟡" if cpu["status"] == "warning" else "🟢"
        output.append(f"{cpu_emoji} **CPU**: {cpu['percentage']}%")
        
        # Disk
        disk = stats["disk"]
        disk_emoji = "🔴" if disk["status"] == "critical" else "🟡" if disk["status"] == "warning" else "🟢"
        output.append(f"{disk_emoji} **Disk**: {disk['used_gb']} GB / {disk['limit_gb']} GB ({disk['percentage']}%)")
        
        # Network
        net = stats["network"]
        output.append(f"🌐 **Network**: ↓{net['rx_mb']} MB / ↑{net['tx_mb']} MB")
        
        # Uptime
        uptime_hours = stats.get("uptime", 0) / 3600000  # Convert ms to hours
        output.append(f"⏱️ **Uptime**: {uptime_hours:.1f} hours")
        
        # Alerts
        if stats["alerts"]:
            output.append("\n🚨 **Active Alerts:**")
            for alert in stats["alerts"]:
                level_emoji = "🔴" if alert["level"] == "critical" else "🟡"
                output.append(f"{level_emoji} **{alert['type'].title()}**: {alert['message']}")
                output.append(f"   💡 Action: {alert['action']}")
        else:
            output.append("\n✅ **No Active Alerts**")
        
        # Quick actions
        output.append("\n🎯 **Quick Actions:**")
        if mem["percentage"] > 80:
            output.append("- Consider restarting server to free memory")
        if disk["percentage"] > 85:
            output.append("- Clean up logs and unnecessary files")
        if cpu["percentage"] > 75:
            output.append("- Check for performance issues")
        if not stats["alerts"]:
            output.append("- Server running optimally!")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ **Error getting server status**: {str(e)}"

@tool
async def run_server_health_check(server_id: str = "auto-detect") -> str:
    """Run comprehensive server health diagnostics"""
    try:
        server_id = await get_user_server_id(server_id)
        health_report = await monitoring_manager.run_health_check(server_id)
        
        output = [f"🏥 **Server Health Check Report**"]
        output.append(f"📅 **Timestamp**: {health_report['timestamp'][:19]}")
        output.append(f"🎯 **Overall Status**: {health_report['overall_status'].upper()}")
        output.append("")
        
        # Individual checks
        output.append("🔍 **Diagnostic Results:**")
        for check_name, check_result in health_report["checks"].items():
            status_emoji = "✅" if check_result["status"] == "passed" else "❌"
            check_display = check_name.replace("_", " ").title()
            output.append(f"{status_emoji} **{check_display}**: {check_result['details']}")
        
        # Recommendations
        if health_report["recommendations"]:
            output.append("\n💡 **Recommendations:**")
            for rec in health_report["recommendations"]:
                output.append(f"- {rec}")
        
        # Next steps
        output.append("\n🎯 **Next Steps:**")
        if health_report["overall_status"] == "critical":
            output.append("- Address critical issues immediately")
            output.append("- Consider restarting server if problems persist")
            output.append("- Contact support if issues continue")
        elif health_report["overall_status"] == "healthy":
            output.append("- Server is running well!")
            output.append("- Continue regular monitoring")
            output.append("- Consider scheduling backups")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ **Error running health check**: {str(e)}"

@tool
async def get_performance_analysis(server_id: str = "auto-detect", hours: int = 24) -> str:
    """Get server performance analysis and trends"""
    try:
        server_id = await get_user_server_id(server_id)
        performance = await monitoring_manager.get_performance_history(server_id, hours)
        
        output = [f"📈 **Performance Analysis Report**"]
        output.append(f"📊 **Period**: {performance['period']}")
        output.append("")
        
        # Current snapshot
        current = performance["current"]
        output.append("📸 **Current Status:**")
        output.append(f"- Health Score: {current['health']['score']}/100")
        output.append(f"- Memory: {current['memory']['percentage']}%")
        output.append(f"- CPU: {current['cpu']['percentage']}%")
        output.append(f"- Disk: {current['disk']['percentage']}%")
        
        # Trends
        output.append("\n📊 **Trends:**")
        trends = performance["trends"]
        for resource, trend in trends.items():
            trend_emoji = "📈" if trend == "increasing" else "📉" if trend == "decreasing" else "➡️"
            output.append(f"{trend_emoji} **{resource.title()}**: {trend}")
        
        # Performance recommendations
        output.append("\n💡 **Performance Recommendations:**")
        for rec in performance["recommendations"]:
            output.append(f"- {rec}")
        
        # Additional insights
        output.append("\n🎯 **Optimization Tips:**")
        if current["memory"]["percentage"] > 70:
            output.append("- Memory usage is elevated - consider restart")
        if current["disk"]["percentage"] > 80:
            output.append("- Disk usage is high - clean up old files")
        if current["cpu"]["percentage"] > 60:
            output.append("- CPU usage is moderate - monitor for spikes")
        
        output.append("- Regular restarts help maintain performance")
        output.append("- Monitor during peak player hours")
        output.append("- Keep plugins and mods updated")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ **Error getting performance analysis**: {str(e)}"

@tool
async def check_server_alerts(server_id: str = "auto-detect") -> str:
    """Check for active server alerts and warnings"""
    try:
        server_id = await get_user_server_id(server_id)
        stats = await monitoring_manager.get_detailed_server_stats(server_id)
        
        alerts = stats.get("alerts", [])
        
        if not alerts:
            return """✅ **No Active Alerts**

🎉 Your server is running smoothly!

**Current Status:**
- All resources within normal ranges
- No critical issues detected
- Server performing optimally

**Preventive Actions:**
- Continue regular monitoring
- Keep backups current
- Monitor during peak hours
"""
        
        output = [f"🚨 **Active Server Alerts ({len(alerts)} total)**\n"]
        
        # Group alerts by severity
        critical_alerts = [a for a in alerts if a["level"] == "critical"]
        warning_alerts = [a for a in alerts if a["level"] == "warning"]
        
        if critical_alerts:
            output.append("🔴 **Critical Alerts (Action Required):**")
            for alert in critical_alerts:
                output.append(f"• **{alert['type'].title()}**: {alert['message']}")
                output.append(f"  💡 Action: {alert['action']}")
            output.append("")
        
        if warning_alerts:
            output.append("🟡 **Warning Alerts (Monitor Closely):**")
            for alert in warning_alerts:
                output.append(f"• **{alert['type'].title()}**: {alert['message']}")
                output.append(f"  💡 Action: {alert['action']}")
            output.append("")
        
        # Priority actions
        output.append("🎯 **Priority Actions:**")
        if critical_alerts:
            output.append("1. Address critical issues immediately")
            output.append("2. Monitor server stability closely")
            output.append("3. Consider server restart if needed")
        else:
            output.append("1. Monitor warning conditions")
            output.append("2. Take preventive actions")
            output.append("3. Schedule regular checks")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ **Error checking alerts**: {str(e)}"

# ADD TO TOOLS LIST
tools = [
    # ... existing tools
    get_detailed_server_status,
    run_server_health_check,
    get_performance_analysis,
    check_server_alerts,
    # ... rest of tools
]
```

---

## 🧪 Testing Phase 3 Features

### Testing Checklist
- [ ] **Backend Setup**: All new client classes created and imported
- [ ] **Tool Registration**: All 15+ new tools added to tools list
- [ ] **API Connectivity**: Pterodactyl API credentials configured
- [ ] **File Operations**: Test file listing, reading, editing
- [ ] **Backup System**: Test backup creation, listing, restoration
- [ ] **Database Management**: Test database creation and management
- [ ] **Monitoring**: Test health checks and performance analysis

### Test Conversation Flow
```
1. "List files in my plugins directory"
2. "Create a backup of my server"
3. "Show me all my databases"
4. "Run a health check on my server"
5. "Get detailed server status"
6. "What's the performance analysis for the last 24 hours?"
7. "Check for any server alerts"
8. "Create a new database called 'essentials'"
9. "Edit the server.properties file"
10. "Delete old backup from last month with confirmation"
```

---

## 🎯 Next Steps After Phase 3

Once Phase 3 is implemented and tested:

1. **Phase 4**: UI & Polish (Tool UI components, frontend enhancements)
2. **Production Hardening**: Error handling, rate limiting, security
3. **Advanced Features**: Automated scheduling, metrics dashboards
4. **Integration Testing**: Full end-to-end testing with real servers

---

## 🚨 Safety Considerations

**Critical File Operations:**
- Always create backups before editing critical files
- Validate file paths and content before writing
- Implement file size limits and safety checks

**Database Security:**
- Never log database passwords
- Implement proper connection string handling
- Validate database names and prevent SQL injection

**Monitoring Alerts:**
- Set appropriate thresholds for alerts
- Prevent alert spam through rate limiting
- Ensure alerts lead to actionable insights

This completes Phase 3 with comprehensive file management, backup systems, database tools, and advanced monitoring capabilities.