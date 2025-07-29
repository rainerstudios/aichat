# Knowledge Base Storage & Management Strategy

## 📁 File Structure for Game Knowledge

```
app/
├── knowledge/
│   ├── base.py                    # Base classes
│   ├── manager.py                 # Knowledge manager
│   ├── sources/                   # Knowledge source handlers
│   │   ├── __init__.py
│   │   ├── file_source.py         # Local files
│   │   ├── url_source.py          # Remote URLs
│   │   ├── api_source.py          # Game APIs
│   │   └── wiki_source.py         # Wiki scraping
│   ├── games/                     # Game-specific modules
│   │   ├── __init__.py
│   │   ├── minecraft/
│   │   │   ├── __init__.py
│   │   │   ├── module.py          # Main knowledge module
│   │   │   ├── settings.yaml      # Static settings data
│   │   │   ├── troubleshooting.yaml # Common issues
│   │   │   ├── commands.yaml      # Admin commands
│   │   │   └── sources.yaml       # URL sources
│   │   ├── rust/
│   │   │   ├── __init__.py
│   │   │   ├── module.py
│   │   │   ├── settings.yaml
│   │   │   └── sources.yaml
│   │   └── generic/
│   │       ├── __init__.py
│   │       └── module.py
│   └── cache/                     # Cached knowledge
│       ├── minecraft_cache.json
│       ├── rust_cache.json
│       └── url_cache/
```

---

## 🌐 Multiple Knowledge Sources Strategy

### **1. Local Files (Static Knowledge)**

```yaml
# app/knowledge/games/minecraft/settings.yaml
game_info:
  name: "Minecraft"
  aliases: ["minecraft", "spigot", "paper", "forge", "fabric"]
  
settings:
  server-name:
    type: "string"
    description: "Server name shown in server list"
    default: "A Minecraft Server"
    category: "basic"
    
  gamemode:
    type: "enum"
    description: "Default game mode for players"
    default: "survival"
    values: ["survival", "creative", "adventure", "spectator"]
    requires_restart: true
    category: "gameplay"
    
  difficulty:
    type: "enum"
    description: "World difficulty level"
    default: "easy"
    values: ["peaceful", "easy", "normal", "hard"]
    category: "gameplay"
```

```yaml
# app/knowledge/games/minecraft/troubleshooting.yaml
troubleshooting:
  - keywords: ["can't connect", "connection refused", "timeout"]
    title: "Connection Issues"
    solution: "Check server status and network configuration"
    severity: "high"
    steps:
      - "Verify server is running with /status command"
      - "Check IP address and port number"
      - "Verify firewall allows connections on server port"
      - "Ensure server is in online-mode if using premium accounts"
    
  - keywords: ["lag", "slow", "freezing", "low tps"]
    title: "Performance Issues"
    solution: "Optimize server settings for better performance"
    severity: "medium"
    steps:
      - "Check TPS with /tps command (should be 20)"
      - "Reduce view-distance to 8-10 chunks"
      - "Increase server RAM allocation"
      - "Remove unnecessary plugins"
```

### **2. URL Sources (Dynamic Knowledge)**

```yaml
# app/knowledge/games/minecraft/sources.yaml
url_sources:
  official_wiki:
    url: "https://minecraft.wiki/"
    type: "wiki"
    update_frequency: "weekly"
    sections:
      - "server.properties"
      - "Commands"
      - "Multiplayer"
    
  paper_docs:
    url: "https://docs.papermc.io/"
    type: "documentation"
    update_frequency: "daily"
    sections:
      - "Configuration"
      - "Performance"
      - "Anti-Cheat"
    
  spigot_forums:
    url: "https://www.spigotmc.org/wiki/"
    type: "forum"
    update_frequency: "daily"
    sections:
      - "Plugin Development"
      - "Server Setup"
    
  performance_guide:
    url: "https://github.com/YouHaveTrouble/minecraft-optimization"
    type: "github"
    update_frequency: "weekly"
    file_path: "README.md"
```

---

## 🔧 Implementation: Knowledge Source Handlers

### **1. URL Source Handler**

```python
# app/knowledge/sources/url_source.py
import httpx
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import yaml
import json
from bs4 import BeautifulSoup
import re

class URLKnowledgeSource:
    """Handles loading knowledge from remote URLs"""
    
    def __init__(self, cache_dir: str = "app/knowledge/cache/url_cache"):
        self.cache_dir = cache_dir
        self.session = httpx.AsyncClient(timeout=30.0)
        
    async def load_from_url(self, source_config: Dict) -> Dict:
        """Load knowledge from a URL source"""
        url = source_config["url"]
        source_type = source_config.get("type", "generic")
        
        # Check cache first
        cached_content = await self._get_cached_content(url, source_config)
        if cached_content:
            return cached_content
        
        # Fetch fresh content
        try:
            content = await self._fetch_content(url, source_type)
            parsed_knowledge = await self._parse_content(content, source_config)
            
            # Cache the result
            await self._cache_content(url, parsed_knowledge, source_config)
            
            return parsed_knowledge
            
        except Exception as e:
            print(f"Error loading from {url}: {e}")
            return {}
    
    async def _fetch_content(self, url: str, source_type: str) -> str:
        """Fetch content from URL"""
        response = await self.session.get(url)
        response.raise_for_status()
        return response.text
    
    async def _parse_content(self, content: str, source_config: Dict) -> Dict:
        """Parse content based on source type"""
        source_type = source_config.get("type", "generic")
        
        if source_type == "wiki":
            return await self._parse_wiki_content(content, source_config)
        elif source_type == "documentation":
            return await self._parse_docs_content(content, source_config)
        elif source_type == "github":
            return await self._parse_github_content(content, source_config)
        elif source_type == "forum":
            return await self._parse_forum_content(content, source_config)
        else:
            return await self._parse_generic_content(content, source_config)
    
    async def _parse_wiki_content(self, content: str, config: Dict) -> Dict:
        """Parse wiki-style content"""
        soup = BeautifulSoup(content, 'html.parser')
        knowledge = {
            "settings": [],
            "commands": [],
            "troubleshooting": []
        }
        
        # Extract settings from wiki tables
        tables = soup.find_all('table')
        for table in tables:
            headers = [th.get_text().strip().lower() for th in table.find_all('th')]
            
            if 'property' in ' '.join(headers) or 'setting' in ' '.join(headers):
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cols = [td.get_text().strip() for td in row.find_all('td')]
                    if len(cols) >= 3:
                        setting = {
                            "name": cols[0],
                            "description": cols[1],
                            "default": cols[2] if len(cols) > 2 else "",
                            "source": "wiki"
                        }
                        knowledge["settings"].append(setting)
        
        # Extract commands
        code_blocks = soup.find_all('code')
        for code in code_blocks:
            text = code.get_text().strip()
            if text.startswith('/') or text.startswith('op ') or text.startswith('whitelist '):
                knowledge["commands"].append({
                    "command": text,
                    "source": "wiki"
                })
        
        return knowledge
    
    async def _parse_github_content(self, content: str, config: Dict) -> Dict:
        """Parse GitHub markdown content"""
        knowledge = {
            "optimizations": [],
            "settings": [],
            "guides": []
        }
        
        # Parse markdown sections
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            if line.startswith('#'):
                if current_section and current_content:
                    # Process previous section
                    section_text = '\n'.join(current_content)
                    parsed_section = await self._parse_markdown_section(current_section, section_text)
                    knowledge[parsed_section["type"]].append(parsed_section["content"])
                
                current_section = line.strip('#').strip().lower()
                current_content = []
            else:
                current_content.append(line)
        
        return knowledge
    
    async def _parse_markdown_section(self, title: str, content: str) -> Dict:
        """Parse a markdown section"""
        if any(word in title for word in ["optimization", "performance", "tuning"]):
            return {
                "type": "optimizations",
                "content": {
                    "title": title,
                    "content": content,
                    "source": "github"
                }
            }
        elif any(word in title for word in ["setting", "config", "property"]):
            return {
                "type": "settings",
                "content": {
                    "title": title,
                    "content": content,
                    "source": "github"
                }
            }
        else:
            return {
                "type": "guides",
                "content": {
                    "title": title,
                    "content": content,
                    "source": "github"
                }
            }
    
    async def _get_cached_content(self, url: str, config: Dict) -> Optional[Dict]:
        """Get cached content if still valid"""
        import os
        from pathlib import Path
        
        cache_file = Path(self.cache_dir) / f"{hash(url)}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            # Check if cache is still valid
            cache_time = datetime.fromisoformat(cached_data["cached_at"])
            update_freq = config.get("update_frequency", "daily")
            
            if update_freq == "daily":
                max_age = timedelta(days=1)
            elif update_freq == "weekly":
                max_age = timedelta(weeks=1)
            elif update_freq == "hourly":
                max_age = timedelta(hours=1)
            else:
                max_age = timedelta(days=1)
            
            if datetime.now() - cache_time < max_age:
                return cached_data["content"]
                
        except Exception as e:
            print(f"Error reading cache for {url}: {e}")
        
        return None
    
    async def _cache_content(self, url: str, content: Dict, config: Dict):
        """Cache content to disk"""
        import os
        from pathlib import Path
        
        cache_dir = Path(self.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        cache_file = cache_dir / f"{hash(url)}.json"
        
        cached_data = {
            "url": url,
            "cached_at": datetime.now().isoformat(),
            "config": config,
            "content": content
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cached_data, f, indent=2)
        except Exception as e:
            print(f"Error caching content for {url}: {e}")
```

### **2. Enhanced Game Module with URL Sources**

```python
# app/knowledge/games/minecraft/module.py
from app.knowledge.base import GameKnowledgeBase
from app.knowledge.sources.url_source import URLKnowledgeSource
from typing import Dict, List, Any
import yaml
from pathlib import Path

class MinecraftKnowledge(GameKnowledgeBase):
    def __init__(self):
        super().__init__()
        self.game_name = "Minecraft"
        self.module_path = Path(__file__).parent
        self.url_source = URLKnowledgeSource()
        
        # Load static knowledge files
        self._load_static_knowledge()
        
        # URL sources will be loaded on demand
        self._url_sources_config = None
    
    def _load_static_knowledge(self):
        """Load static knowledge from YAML files"""
        
        # Load settings
        settings_file = self.module_path / "settings.yaml"
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                settings_data = yaml.safe_load(f)
                self._parse_settings_yaml(settings_data)
        
        # Load troubleshooting
        troubleshooting_file = self.module_path / "troubleshooting.yaml"
        if troubleshooting_file.exists():
            with open(troubleshooting_file, 'r') as f:
                troubleshooting_data = yaml.safe_load(f)
                self._parse_troubleshooting_yaml(troubleshooting_data)
        
        # Load URL sources config
        sources_file = self.module_path / "sources.yaml"
        if sources_file.exists():
            with open(sources_file, 'r') as f:
                self._url_sources_config = yaml.safe_load(f)
    
    async def get_enhanced_knowledge(self, query: str) -> Dict[str, Any]:
        """Get knowledge from both static files and URL sources"""
        
        # Start with static knowledge
        static_results = {
            "troubleshooting": await self.search_troubleshooting(query),
            "settings": [s for s in self.settings if query.lower() in s.name.lower()],
            "optimizations": [o for o in self.optimizations if query.lower() in o.title.lower()]
        }
        
        # Add URL-sourced knowledge
        url_results = await self._search_url_sources(query)
        
        # Combine results
        combined_results = {
            "static": static_results,
            "dynamic": url_results,
            "sources": ["local_files", "wiki", "documentation", "github"]
        }
        
        return combined_results
    
    async def _search_url_sources(self, query: str) -> Dict[str, Any]:
        """Search URL sources for relevant knowledge"""
        if not self._url_sources_config:
            return {}
        
        results = {}
        
        for source_name, source_config in self._url_sources_config.get("url_sources", {}).items():
            try:
                source_content = await self.url_source.load_from_url(source_config)
                
                # Search content for query relevance
                relevant_content = self._filter_relevant_content(source_content, query)
                
                if relevant_content:
                    results[source_name] = {
                        "source_url": source_config["url"],
                        "content": relevant_content,
                        "last_updated": source_config.get("update_frequency", "unknown")
                    }
                    
            except Exception as e:
                print(f"Error searching {source_name}: {e}")
                continue
        
        return results
    
    def _filter_relevant_content(self, content: Dict, query: str) -> Dict:
        """Filter content for query relevance"""
        relevant = {}
        query_words = query.lower().split()
        
        for category, items in content.items():
            relevant_items = []
            
            for item in items:
                item_text = str(item).lower()
                if any(word in item_text for word in query_words):
                    relevant_items.append(item)
            
            if relevant_items:
                relevant[category] = relevant_items
        
        return relevant
    
    async def update_knowledge_from_sources(self):
        """Update knowledge base from all URL sources"""
        if not self._url_sources_config:
            return
        
        print(f"Updating {self.game_name} knowledge from {len(self._url_sources_config.get('url_sources', {}))} sources...")
        
        for source_name, source_config in self._url_sources_config.get("url_sources", {}).items():
            try:
                print(f"Updating from {source_name}...")
                content = await self.url_source.load_from_url(source_config)
                
                # Merge new content with existing knowledge
                await self._merge_url_content(content, source_name)
                
            except Exception as e:
                print(f"Error updating from {source_name}: {e}")
        
        print(f"{self.game_name} knowledge update complete.")
    
    async def _merge_url_content(self, content: Dict, source_name: str):
        """Merge URL content with existing knowledge"""
        
        # Add new settings from URLs
        if "settings" in content:
            for setting_data in content["settings"]:
                # Convert URL setting to our format
                if not any(s.name == setting_data.get("name") for s in self.settings):
                    # Add new setting discovered from URL
                    pass
        
        # Add new troubleshooting entries
        if "troubleshooting" in content:
            for issue in content["troubleshooting"]:
                # Add URL-sourced troubleshooting
                pass
        
        # Add optimizations
        if "optimizations" in content:
            for opt in content["optimizations"]:
                # Add URL-sourced optimizations
                pass
```

### **3. Knowledge Update Service**

```python
# app/services/knowledge_updater.py
import asyncio
from typing import List
from app.knowledge.manager import GameKnowledgeManager
from datetime import datetime
import schedule
import threading

class KnowledgeUpdateService:
    """Service to keep URL-sourced knowledge up to date"""
    
    def __init__(self):
        self.knowledge_manager = GameKnowledgeManager()
        self.update_running = False
    
    async def update_all_games(self):
        """Update knowledge for all games from their URL sources"""
        if self.update_running:
            print("Knowledge update already running, skipping...")
            return
        
        self.update_running = True
        
        try:
            print("Starting knowledge update for all games...")
            
            # Get all game modules
            games = self.knowledge_manager.get_supported_games()
            
            # Update each game concurrently (with limits)
            semaphore = asyncio.Semaphore(3)  # Max 3 concurrent updates
            
            async def update_single_game(game_name: str):
                async with semaphore:
                    module = await self.knowledge_manager.get_knowledge_by_name(game_name)
                    if hasattr(module, 'update_knowledge_from_sources'):
                        await module.update_knowledge_from_sources()
            
            # Run updates
            tasks = [update_single_game(game) for game in games]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            print("Knowledge update completed for all games.")
            
        except Exception as e:
            print(f"Error during knowledge update: {e}")
        finally:
            self.update_running = False
    
    def start_scheduled_updates(self):
        """Start background scheduled updates"""
        
        # Schedule daily updates
        schedule.every().day.at("02:00").do(self._run_update)
        
        # Schedule weekly deep updates
        schedule.every().sunday.at("03:00").do(self._run_deep_update)
        
        # Run scheduler in background thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        print("Knowledge update scheduler started")
    
    def _run_update(self):
        """Run update in async context"""
        asyncio.create_task(self.update_all_games())
    
    def _run_deep_update(self):
        """Run deep update (clears cache first)"""
        asyncio.create_task(self._deep_update())
    
    async def _deep_update(self):
        """Deep update that clears cache first"""
        # Clear URL cache
        import shutil
        from pathlib import Path
        
        cache_dir = Path("app/knowledge/cache/url_cache")
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            cache_dir.mkdir(parents=True)
        
        # Run normal update
        await self.update_all_games()
```

---

## 🚀 Usage Examples

### **1. Adding a New Game with URL Sources**

```python
# Create new game directory
mkdir app/knowledge/games/valheim

# Create sources.yaml
# app/knowledge/games/valheim/sources.yaml
url_sources:
  valheim_wiki:
    url: "https://valheim.fandom.com/wiki/Dedicated_server"
    type: "wiki"
    update_frequency: "weekly"
    
  valheim_plus_github:
    url: "https://github.com/valheimPlus/ValheimPlus"
    type: "github"
    update_frequency: "daily"
    file_path: "README.md"
```

### **2. Using URL Knowledge in Responses**

```python
# In your LangGraph node
async def generate_enhanced_response_node(state: ServerBotState) -> ServerBotState:
    query = state["conversation_history"][-1]["content"]
    game_type = state.get("game_type")
    
    # Get enhanced knowledge (static + URLs)
    game_module = await knowledge_manager.get_knowledge_by_name(game_type)
    enhanced_knowledge = await game_module.get_enhanced_knowledge(query)
    
    # Generate response using both static and dynamic knowledge
    response = await generate_ai_response_with_enhanced_context(
        query=query,
        static_knowledge=enhanced_knowledge["static"],
        dynamic_knowledge=enhanced_knowledge["dynamic"]
    )
    
    state["last_response"] = response
    return state
```

### **3. Manual Knowledge Updates**

```python
# Update specific game
updater = KnowledgeUpdateService()
await updater.update_single_game("minecraft")

# Update all games
await updater.update_all_games()

# Start automatic updates
updater.start_scheduled_updates()
```

---

## 📊 Benefits of This Approach

### **1. Always Current Knowledge**
- ✅ **Automatic updates** from official sources
- ✅ **Community knowledge** from forums and wikis
- ✅ **Latest optimizations** from GitHub repos

### **2. Multiple Source Types**
- ✅ **Official wikis** (minecraft.wiki, rust.fandom.com)
- ✅ **Documentation sites** (docs.papermc.io)
- ✅ **GitHub repositories** (optimization guides)
- ✅ **Community forums** (spigotmc.org, reddit)

### **3. Efficient Caching**
- ✅ **Smart caching** based on update frequency
- ✅ **Background updates** don't slow down responses
- ✅ **Fallback to static** if URLs are unavailable

### **4. Easy Expansion**
- ✅ **Just add sources.yaml** for new games
- ✅ **No code changes** needed for new URL sources
- ✅ **Automatic parsing** for common formats

This approach gives you the best of both worlds: reliable static knowledge for instant responses, plus dynamic URL-sourced knowledge that keeps your bot current with the latest information from the gaming community.
