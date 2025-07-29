# 📋 Phase 2: Smart Contextual Features Implementation
*Timeline: Week 3-4 | Add game-specific intelligence and advanced troubleshooting*

## Overview
Phase 2 builds intelligent features on top of the Phase 1 foundation, adding game detection, contextual knowledge, smart troubleshooting, and enhanced safety mechanisms.

---

## 🎯 Phase 2 Goals
- ✅ Automatic game detection and context switching
- ✅ Game-specific knowledge modules (starting with top 10 games)
- ✅ Smart troubleshooting system with diagnostic tools
- ✅ Enhanced safety mechanisms with operation confirmations
- ✅ Server optimization recommendations engine
- ✅ Context-aware responses based on server state

---

## 📦 Week 3: Game Intelligence System

### ✅ Task 2.1: Game Detection and Knowledge Framework (Day 1-2)

#### Step 1: Create Game Detection Service
- [ ] **File**: `backend/app/services/game_detector.py`
- [ ] **Action**: Create comprehensive game detection system

```python
from typing import Dict, Optional, List, Any
import re
from dataclasses import dataclass
from enum import Enum

class GameCategory(Enum):
    SURVIVAL = "survival"
    SANDBOX = "sandbox" 
    FPS = "fps"
    STRATEGY = "strategy"
    RPG = "rpg"
    RACING = "racing"
    SIMULATION = "simulation"
    MMO = "mmo"
    UNKNOWN = "unknown"

@dataclass
class GameInfo:
    name: str
    category: GameCategory
    default_ports: List[int]
    common_configs: List[str]
    optimization_focus: str
    player_impact_level: str  # low, medium, high
    supports_mods: bool
    has_whitelist: bool
    has_console_commands: bool

class GameDetector:
    """
    Detects game type from server information and provides game-specific context
    """
    
    def __init__(self):
        self.game_patterns = {
            # Minecraft variants
            "minecraft": {
                "patterns": [
                    r"minecraft.*java",
                    r"paper.*server", 
                    r"spigot.*server",
                    r"forge.*server",
                    r"fabric.*server",
                    r"bukkit.*server",
                    r"vanilla.*minecraft"
                ],
                "info": GameInfo(
                    name="Minecraft Java Edition",
                    category=GameCategory.SANDBOX,
                    default_ports=[25565],
                    common_configs=["server.properties", "bukkit.yml", "spigot.yml"],
                    optimization_focus="memory_management",
                    player_impact_level="high",
                    supports_mods=True,
                    has_whitelist=True,
                    has_console_commands=True
                )
            },
            
            "minecraft_bedrock": {
                "patterns": [
                    r"minecraft.*bedrock",
                    r"bedrock.*server",
                    r"pocketmine",
                    r"nukkit"
                ],
                "info": GameInfo(
                    name="Minecraft Bedrock Edition",
                    category=GameCategory.SANDBOX,
                    default_ports=[19132],
                    common_configs=["server.properties", "permissions.yml"],
                    optimization_focus="network_optimization",
                    player_impact_level="high",
                    supports_mods=False,
                    has_whitelist=True,
                    has_console_commands=True
                )
            },
            
            # Rust
            "rust": {
                "patterns": [
                    r"rust.*server",
                    r"oxide.*rust",
                    r"carbon.*rust"
                ],
                "info": GameInfo(
                    name="Rust",
                    category=GameCategory.SURVIVAL,
                    default_ports=[28015, 28016],
                    common_configs=["server.cfg", "oxide/config"],
                    optimization_focus="cpu_performance",
                    player_impact_level="high",
                    supports_mods=True,
                    has_whitelist=False,
                    has_console_commands=True
                )
            },
            
            # ARK Survival Evolved
            "ark": {
                "patterns": [
                    r"ark.*survival",
                    r"shootergame.*server",
                    r"ark.*server"
                ],
                "info": GameInfo(
                    name="ARK: Survival Evolved",
                    category=GameCategory.SURVIVAL,
                    default_ports=[7777, 7778, 27015],
                    common_configs=["GameUserSettings.ini", "Game.ini"],
                    optimization_focus="memory_and_cpu",
                    player_impact_level="high",
                    supports_mods=True,
                    has_whitelist=True,
                    has_console_commands=True
                )
            },
            
            # 7 Days to Die
            "7d2d": {
                "patterns": [
                    r"7.*days.*die",
                    r"7dtd.*server",
                    r"dedicated.*7d2d"
                ],
                "info": GameInfo(
                    name="7 Days to Die",
                    category=GameCategory.SURVIVAL,
                    default_ports=[26900, 26901, 26902],
                    common_configs=["serverconfig.xml", "serveradmin.xml"],
                    optimization_focus="memory_management",
                    player_impact_level="medium",
                    supports_mods=True,
                    has_whitelist=True,
                    has_console_commands=True
                )
            },
            
            # Valheim
            "valheim": {
                "patterns": [
                    r"valheim.*server",
                    r"valheim.*dedicated"
                ],
                "info": GameInfo(
                    name="Valheim",
                    category=GameCategory.SURVIVAL,
                    default_ports=[2456, 2457, 2458],
                    common_configs=[],
                    optimization_focus="network_stability",
                    player_impact_level="medium",
                    supports_mods=True,
                    has_whitelist=False,
                    has_console_commands=True
                )
            },
            
            # CS2 / CS:GO
            "cs2": {
                "patterns": [
                    r"counter.*strike.*2",
                    r"cs2.*server",
                    r"csgo.*server",
                    r"source.*dedicated"
                ],
                "info": GameInfo(
                    name="Counter-Strike 2",
                    category=GameCategory.FPS,
                    default_ports=[27015, 27020],
                    common_configs=["server.cfg", "autoexec.cfg"],
                    optimization_focus="tick_rate",
                    player_impact_level="high",
                    supports_mods=True,
                    has_whitelist=False,
                    has_console_commands=True
                )
            },
            
            # Garry's Mod
            "gmod": {
                "patterns": [
                    r"garry.*mod",
                    r"gmod.*server",
                    r"garrysmod"
                ],
                "info": GameInfo(
                    name="Garry's Mod",
                    category=GameCategory.SANDBOX,
                    default_ports=[27015],
                    common_configs=["server.cfg", "autoexec.cfg"],
                    optimization_focus="addon_management",
                    player_impact_level="medium",
                    supports_mods=True,
                    has_whitelist=False,
                    has_console_commands=True
                )
            },
            
            # Palworld
            "palworld": {
                "patterns": [
                    r"palworld.*server",
                    r"pal.*world.*dedicated"
                ],
                "info": GameInfo(
                    name="Palworld",
                    category=GameCategory.SURVIVAL,
                    default_ports=[8211],
                    common_configs=["PalWorldSettings.ini"],
                    optimization_focus="memory_management",
                    player_impact_level="medium",
                    supports_mods=False,
                    has_whitelist=False,
                    has_console_commands=True
                )
            },
            
            # Terraria
            "terraria": {
                "patterns": [
                    r"terraria.*server",
                    r"tshock.*server"
                ],
                "info": GameInfo(
                    name="Terraria",
                    category=GameCategory.SANDBOX,
                    default_ports=[7777],
                    common_configs=["config.json", "tshock/config.json"],
                    optimization_focus="world_management",
                    player_impact_level="low",
                    supports_mods=True,
                    has_whitelist=True,
                    has_console_commands=True
                )
            }
        }
    
    def detect_game(self, server_info: Dict[str, Any]) -> GameInfo:
        """
        Detect game type from server information
        """
        # Get egg information
        egg_info = server_info.get("egg", {})
        egg_name = egg_info.get("name", "").lower()
        egg_description = egg_info.get("description", "").lower()
        server_name = server_info.get("name", "").lower()
        
        # Combine all text for pattern matching
        search_text = f"{egg_name} {egg_description} {server_name}"
        
        # Try to match against known patterns
        for game_key, game_data in self.game_patterns.items():
            for pattern in game_data["patterns"]:
                if re.search(pattern, search_text, re.IGNORECASE):
                    return game_data["info"]
        
        # Default fallback
        return GameInfo(
            name="Unknown Game",
            category=GameCategory.UNKNOWN,
            default_ports=[],
            common_configs=[],
            optimization_focus="general_performance",
            player_impact_level="medium",
            supports_mods=False,
            has_whitelist=False,
            has_console_commands=True
        )
    
    def get_game_specific_advice(self, game_info: GameInfo, issue_type: str) -> List[str]:
        """
        Get game-specific advice for common issues
        """
        advice_db = {
            ("minecraft", "performance"): [
                "Reduce view-distance in server.properties (8-12 recommended)",
                "Use Paper or Fabric for better performance than Vanilla",
                "Add more RAM (4-8GB recommended for 10-20 players)",
                "Limit entity spawning and mob farms",
                "Use optimization plugins like ClearLagg"
            ],
            ("minecraft", "lag"): [
                "Check TPS with /tps command (should be 20.0)",
                "Reduce loaded chunks by limiting world borders",
                "Remove laggy plugins or optimize configurations",
                "Increase server RAM allocation",
                "Use /timings report to identify lag sources"
            ],
            ("rust", "performance"): [
                "Adjust population.* convars for better performance",
                "Limit bag despawn time to reduce world save size",
                "Use smaller map sizes (2000-3000 recommended)",
                "Optimize graphics.itemskins and other visual settings",
                "Regular map wipes help maintain performance"
            ],
            ("ark", "crashes"): [
                "Increase memory allocation (16GB+ recommended)",
                "Disable or limit structure limit per platform",
                "Use smaller maps or reduce max players",
                "Regular saves and restarts prevent memory leaks",
                "Check for incompatible mod combinations"
            ]
        }
        
        game_key = game_info.name.lower().split()[0]  # First word of game name
        key = (game_key, issue_type.lower())
        
        return advice_db.get(key, [
            "Check server logs for specific error messages",
            "Verify server resources (CPU, RAM, disk space)",
            "Restart server to clear temporary issues",
            "Update to latest game version if available"
        ])
    
    def get_optimization_tips(self, game_info: GameInfo, server_resources: Dict[str, Any]) -> List[str]:
        """
        Get optimization recommendations based on game and current resource usage
        """
        tips = []
        
        cpu_usage = server_resources.get("cpu_absolute", 0)
        memory_usage = server_resources.get("memory_bytes", 0)
        memory_limit = server_resources.get("memory_limit", 1024 * 1024 * 1024)  # Default 1GB
        
        memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
        
        # General resource optimization
        if cpu_usage > 80:
            tips.append("🔥 **High CPU Usage**: Consider reducing tick rate or player count")
        
        if memory_percent > 85:
            tips.append("💾 **High Memory Usage**: Increase RAM allocation or optimize world size")
        
        # Game-specific optimization
        if game_info.category == GameCategory.SANDBOX:
            if memory_percent > 70:
                tips.append("🏗️ **Sandbox Game**: Limit structure/building complexity to reduce memory usage")
            tips.append("🗺️ **World Size**: Consider periodic world resets or using world borders")
        
        elif game_info.category == GameCategory.SURVIVAL:
            tips.append("🎒 **Inventory Management**: Regular cleanups of dropped items improve performance")
            tips.append("🏠 **Base Limits**: Limit bases per player to prevent lag accumulation")
        
        elif game_info.category == GameCategory.FPS:
            tips.append("⚡ **Tick Rate**: Ensure consistent tick rate for competitive gameplay")
            tips.append("📊 **Player Statistics**: Monitor hit registration and ping consistency")
        
        # Mod-specific advice
        if game_info.supports_mods:
            tips.append("🔧 **Mod Management**: Regularly audit and remove unused mods")
            tips.append("🔄 **Mod Updates**: Keep mods updated for compatibility and performance")
        
        return tips if tips else ["✅ **Server Performance**: Resources look healthy, no immediate optimization needed"]

# Global game detector instance
game_detector = GameDetector()
```

#### Step 2: Create Game Knowledge Module System
- [ ] **File**: `backend/app/knowledge/__init__.py`
- [ ] **Action**: Create knowledge module framework

```python
# CREATE NEW FILE
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from ..services.game_detector import GameInfo

class GameKnowledgeModule(ABC):
    """
    Abstract base class for game-specific knowledge modules
    """
    
    def __init__(self, game_info: GameInfo):
        self.game_info = game_info
    
    @abstractmethod
    def get_troubleshooting_steps(self, issue: str) -> List[str]:
        """Get step-by-step troubleshooting for specific issues"""
        pass
    
    @abstractmethod  
    def get_configuration_advice(self, scenario: str) -> Dict[str, Any]:
        """Get recommended configuration for scenarios (pvp, pve, creative, etc.)"""
        pass
    
    @abstractmethod
    def validate_server_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate server configuration and return warnings"""
        pass
    
    @abstractmethod
    def get_performance_recommendations(self, resources: Dict[str, Any]) -> List[str]:
        """Get performance optimization recommendations"""
        pass
    
    def supports_feature(self, feature: str) -> bool:
        """Check if game supports specific features"""
        feature_map = {
            "whitelist": self.game_info.has_whitelist,
            "mods": self.game_info.supports_mods,
            "console": self.game_info.has_console_commands
        }
        return feature_map.get(feature, False)
```

#### Step 3: Create Minecraft Knowledge Module (Example Implementation)
- [ ] **File**: `backend/app/knowledge/minecraft.py`
- [ ] **Action**: Create comprehensive Minecraft knowledge

```python
from typing import Dict, List, Any, Optional
from . import GameKnowledgeModule
from ..services.game_detector import GameInfo

class MinecraftKnowledgeModule(GameKnowledgeModule):
    """
    Comprehensive knowledge module for Minecraft server management
    """
    
    def __init__(self, game_info: GameInfo):
        super().__init__(game_info)
        
        # Minecraft-specific configuration templates
        self.scenario_configs = {
            "survival_pve": {
                "difficulty": "normal",
                "pvp": "false",
                "spawn-protection": "16", 
                "keep-inventory": "false",
                "mob-spawning": "true",
                "view-distance": "10"
            },
            "survival_pvp": {
                "difficulty": "hard",
                "pvp": "true",
                "spawn-protection": "0",
                "keep-inventory": "false", 
                "mob-spawning": "true",
                "view-distance": "8"
            },
            "creative": {
                "gamemode": "creative",
                "difficulty": "peaceful",
                "pvp": "false",
                "spawn-protection": "0",
                "keep-inventory": "true",
                "mob-spawning": "false",
                "view-distance": "12"
            },
            "hardcore": {
                "difficulty": "hard",
                "hardcore": "true",
                "pvp": "true",
                "spawn-protection": "0",
                "keep-inventory": "false",
                "mob-spawning": "true",
                "view-distance": "6"
            }
        }
    
    def get_troubleshooting_steps(self, issue: str) -> List[str]:
        """Minecraft-specific troubleshooting steps"""
        
        issue_lower = issue.lower()
        
        if "lag" in issue_lower or "tps" in issue_lower or "slow" in issue_lower:
            return [
                "1. **Check TPS**: Run `/tps` command (should be 20.0)",
                "2. **Check View Distance**: Reduce in server.properties (8-10 recommended)",
                "3. **Monitor Entities**: Use `/minecraft:kill` to remove excess entities",
                "4. **Check Plugins**: Disable recently added plugins to test",
                "5. **Increase RAM**: Ensure 4-8GB RAM for 10-20 players",
                "6. **Use Timings**: Run `/timings report` to identify lag sources",
                "7. **World Border**: Limit world size to reduce chunk loading"
            ]
        
        elif "crash" in issue_lower or "stop" in issue_lower:
            return [
                "1. **Check Logs**: Look in `logs/latest.log` for error messages",
                "2. **Memory Check**: Ensure sufficient RAM allocation (4GB minimum)",
                "3. **Plugin Conflicts**: Test with plugins disabled",
                "4. **Java Version**: Update to latest Java 17 or 21",
                "5. **Mod Compatibility**: Check mod versions match server version",
                "6. **Backup Restore**: Restore from last working backup if needed",
                "7. **Clean Start**: Try fresh server files if corruption suspected"
            ]
        
        elif "connect" in issue_lower or "join" in issue_lower:
            return [
                "1. **Server Status**: Verify server is running and accessible",
                "2. **Port Forwarding**: Check port 25565 is open",
                "3. **Whitelist**: If enabled, ensure player is whitelisted",
                "4. **Version Match**: Client and server versions must match",
                "5. **IP Address**: Verify correct server IP/domain",
                "6. **Firewall**: Check server firewall allows Minecraft",
                "7. **Max Players**: Ensure server isn't at player limit"
            ]
        
        elif "griefing" in issue_lower or "protection" in issue_lower:
            return [
                "1. **WorldGuard**: Install protection plugin for regions",
                "2. **Backup Regularly**: Enable automatic backups",
                "3. **CoreProtect**: Install for block logging and rollbacks",
                "4. **Whitelist**: Enable whitelist for private servers", 
                "5. **Spawn Protection**: Increase spawn-protection radius",
                "6. **Admin Tools**: Use `/gamemode spectator` to investigate",
                "7. **Ban Management**: Use `/ban` and `/ban-ip` for griefers"
            ]
        
        else:
            return [
                "1. **Check Server Status**: Verify server is running properly",
                "2. **Review Logs**: Look in logs/ directory for error messages",
                "3. **Resource Usage**: Check CPU and RAM usage",
                "4. **Recent Changes**: Consider what was changed recently",
                "5. **Backup**: Restore from backup if issue persists",
                "6. **Plugin/Mod Test**: Disable additions to isolate issue",
                "7. **Community Help**: Check Minecraft server forums for specific issue"
            ]
    
    def get_configuration_advice(self, scenario: str) -> Dict[str, Any]:
        """Get recommended Minecraft configuration for different scenarios"""
        
        base_config = self.scenario_configs.get(scenario.lower(), {})
        
        # Add scenario-specific advice
        advice = {
            "config": base_config,
            "plugins": [],
            "performance_tips": [],
            "security_tips": []
        }
        
        if scenario.lower() == "survival_pve":
            advice["plugins"] = ["EssentialsX", "WorldGuard", "LuckPerms", "CoreProtect"]
            advice["performance_tips"] = [
                "Set view-distance to 10 for good balance",
                "Enable spawn-protection for safety",
                "Use Paper/Spigot for better performance"
            ]
            advice["security_tips"] = [
                "Enable whitelist for private servers",
                "Regular backups every 4-6 hours",
                "Install anti-grief plugins"
            ]
        
        elif scenario.lower() == "survival_pvp":
            advice["plugins"] = ["EssentialsX", "Factions", "McMMO", "CombatLogX"]
            advice["performance_tips"] = [
                "Reduce view-distance to 8 for more players",
                "Disable spawn-protection for PvP",
                "Monitor for combat exploits"
            ]
            advice["security_tips"] = [
                "Strong anti-cheat plugins required",
                "Regular map resets to prevent hoarding", 
                "IP-based banning for serious offenses"
            ]
        
        elif scenario.lower() == "creative":
            advice["plugins"] = ["WorldEdit", "VoxelSniper", "PlotSquared", "AsyncWorldEdit"]
            advice["performance_tips"] = [
                "Higher view-distance acceptable (12-16)",
                "Disable mob spawning to save resources",
                "Set peaceful difficulty"
            ]
            advice["security_tips"] = [
                "Limit WorldEdit usage for non-ops",
                "Regular world backups before big builds",
                "Consider separate creative world"
            ]
        
        return advice
    
    def validate_server_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate Minecraft server configuration"""
        warnings = []
        
        # Check memory allocation
        max_players = int(config.get("max-players", 20))
        if max_players > 50:
            warnings.append("⚠️ High player count (>50) requires significant RAM (8GB+)")
        
        # Check view distance vs players
        view_distance = int(config.get("view-distance", 10))
        if view_distance > 16:
            warnings.append("⚠️ View distance >16 causes significant performance impact")
        elif view_distance * max_players > 300:  # Rough heuristic
            warnings.append(f"⚠️ View distance ({view_distance}) too high for {max_players} players")
        
        # Check difficulty settings
        difficulty = config.get("difficulty", "normal")
        pvp = config.get("pvp", "false")
        if difficulty == "peaceful" and pvp == "true":
            warnings.append("⚠️ PvP enabled with peaceful difficulty - players can't be damaged")
        
        # Check spawn protection
        spawn_protection = int(config.get("spawn-protection", 16))
        if pvp == "true" and spawn_protection > 0:
            warnings.append("⚠️ Spawn protection may interfere with PvP gameplay")
        
        # Check resource pack settings
        if config.get("resource-pack-prompt"):
            warnings.append("ℹ️ Resource pack prompt may cause connection delays")
        
        return warnings
    
    def get_performance_recommendations(self, resources: Dict[str, Any]) -> List[str]:
        """Minecraft-specific performance recommendations"""
        
        recommendations = []
        
        cpu_usage = resources.get("cpu_absolute", 0)
        memory_usage = resources.get("memory_bytes", 0) 
        memory_limit = resources.get("memory_limit", 2 * 1024**3)  # 2GB default
        
        memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
        
        # CPU-specific recommendations
        if cpu_usage > 80:
            recommendations.extend([
                "🔥 **High CPU**: Reduce view-distance to 6-8",
                "⚡ **Optimization**: Switch to Paper or Fabric for better performance",
                "👥 **Player Limit**: Consider reducing max-players temporarily",
                "🗺️ **World Border**: Limit world size to reduce chunk generation",
                "🐄 **Entity Limits**: Reduce mob spawning and entity counts"
            ])
        
        # Memory-specific recommendations  
        if memory_percent > 85:
            recommendations.extend([
                "💾 **High Memory**: Increase RAM allocation (4-8GB recommended)",
                "🧹 **Garbage Collection**: Add JVM flags: -XX:+UseG1GC -XX:+UnlockExperimentalVMOptions",
                "🏗️ **World Size**: Consider world resets or pruning unused chunks",
                "📦 **Plugin Audit**: Remove unused plugins to free memory",
                "🎒 **Item Cleanup**: Use plugins like ClearLagg for dropped items"
            ])
        
        elif memory_percent < 30:
            recommendations.append("✅ **Memory Healthy**: Current memory usage is optimal")
        
        # General Minecraft optimizations
        if cpu_usage > 60 or memory_percent > 70:
            recommendations.extend([
                "🔧 **server.properties**: Set network-compression-threshold=512",
                "📊 **Monitoring**: Use `/tps` and `/timings` commands regularly",
                "🎮 **Server Software**: Consider PaperMC for performance improvements",
                "⏰ **Restart Schedule**: Implement 12-24 hour restart schedule"
            ])
        
        # Add positive feedback if performance is good
        if cpu_usage < 50 and memory_percent < 60:
            recommendations.append("🎉 **Performance Excellent**: Server resources are well-optimized!")
        
        return recommendations if recommendations else [
            "✅ **Performance Good**: No immediate optimizations needed",
            "📈 **Monitoring**: Continue monitoring during peak player times"
        ]
    
    def get_command_suggestions(self, context: str) -> List[str]:
        """Get Minecraft command suggestions based on context"""
        
        context_lower = context.lower()
        
        if "player" in context_lower:
            return [
                "/whitelist add <player> - Add player to whitelist",
                "/op <player> - Give player operator permissions", 
                "/gamemode <mode> <player> - Change player gamemode",
                "/tp <player1> <player2> - Teleport players",
                "/ban <player> - Ban a player",
                "/kick <player> - Kick player from server"
            ]
        
        elif "world" in context_lower or "time" in context_lower:
            return [
                "/time set day - Set time to day",
                "/time set night - Set time to night",
                "/weather clear - Clear weather",
                "/difficulty <level> - Change difficulty",
                "/gamerule <rule> <value> - Change game rules",
                "/worldborder set <size> - Set world border"
            ]
        
        elif "performance" in context_lower or "lag" in context_lower:
            return [
                "/tps - Check server tick rate",
                "/timings report - Generate performance report",
                "/minecraft:kill @e[type=item] - Remove dropped items",
                "/forge entity list - List entity counts (Forge)",
                "/gc - Force garbage collection (some plugins)"
            ]
        
        else:
            return [
                "/help - Show available commands",
                "/list - List online players", 
                "/save-all - Save world data",
                "/reload - Reload server configuration",
                "/version - Show server version",
                "/plugins - List installed plugins"
            ]

# Factory function
def create_minecraft_knowledge(game_info: GameInfo) -> MinecraftKnowledgeModule:
    return MinecraftKnowledgeModule(game_info)
```

#### Step 4: Create Knowledge Manager Service
- [ ] **File**: `backend/app/services/knowledge_manager.py`
- [ ] **Action**: Create knowledge management system

```python
from typing import Dict, Optional, List, Any
from ..services.game_detector import GameDetector, GameInfo
from ..knowledge import GameKnowledgeModule
from ..knowledge.minecraft import create_minecraft_knowledge

class KnowledgeManager:
    """
    Manages game-specific knowledge modules and provides contextual intelligence
    """
    
    def __init__(self):
        self.game_detector = GameDetector()
        self.knowledge_cache: Dict[str, GameKnowledgeModule] = {}
        
        # Registry of knowledge modules
        self.module_registry = {
            "minecraft java edition": create_minecraft_knowledge,
            "minecraft bedrock edition": create_minecraft_knowledge,
            # Add more modules as they're implemented
        }
    
    def get_game_knowledge(self, server_info: Dict[str, Any]) -> GameKnowledgeModule:
        """
        Get appropriate knowledge module for server
        """
        game_info = self.game_detector.detect_game(server_info)
        game_key = game_info.name.lower()
        
        # Check cache first
        if game_key in self.knowledge_cache:
            return self.knowledge_cache[game_key]
        
        # Create new knowledge module
        module_factory = self.module_registry.get(game_key)
        if module_factory:
            knowledge_module = module_factory(game_info)
        else:
            # Use generic knowledge module
            knowledge_module = GenericGameKnowledge(game_info)
        
        # Cache for reuse
        self.knowledge_cache[game_key] = knowledge_module
        return knowledge_module
    
    def get_contextual_advice(self, server_info: Dict[str, Any], 
                            resources: Dict[str, Any], 
                            issue: str) -> Dict[str, Any]:
        """
        Get comprehensive advice combining game detection, resources, and issue analysis
        """
        game_info = self.game_detector.detect_game(server_info)
        knowledge_module = self.get_game_knowledge(server_info)
        
        return {
            "game_info": {
                "name": game_info.name,
                "category": game_info.category.value,
                "supports_mods": game_info.supports_mods,
                "has_whitelist": game_info.has_whitelist,
                "player_impact": game_info.player_impact_level
            },
            "troubleshooting_steps": knowledge_module.get_troubleshooting_steps(issue),
            "performance_tips": knowledge_module.get_performance_recommendations(resources),
            "optimization_focus": game_info.optimization_focus,
            "safety_warnings": self._get_safety_warnings(game_info, issue)
        }
    
    def _get_safety_warnings(self, game_info: GameInfo, issue: str) -> List[str]:
        """Generate safety warnings based on game type and issue"""
        warnings = []
        
        if game_info.player_impact_level == "high":
            warnings.append("⚠️ This game has HIGH player impact - changes may disconnect players")
        
        if "restart" in issue.lower() or "stop" in issue.lower():
            warnings.append("🚨 Server restart/stop will disconnect all players immediately")
        
        if game_info.supports_mods and "mod" in issue.lower():
            warnings.append("🔧 Mod changes may require server restart and client updates")
        
        return warnings

class GenericGameKnowledge(GameKnowledgeModule):
    """Generic knowledge module for unknown games"""
    
    def get_troubleshooting_steps(self, issue: str) -> List[str]:
        return [
            "1. **Check Server Status**: Verify server is running properly",
            "2. **Review Logs**: Look for error messages in server logs",
            "3. **Resource Usage**: Monitor CPU, RAM, and disk usage", 
            "4. **Network Check**: Verify network connectivity and ports",
            "5. **Recent Changes**: Consider what was modified recently",
            "6. **Restart Test**: Try restarting server to clear temporary issues",
            "7. **Support Documentation**: Check game-specific documentation"
        ]
    
    def get_configuration_advice(self, scenario: str) -> Dict[str, Any]:
        return {
            "config": {},
            "advice": [
                "Check game-specific documentation for configuration options",
                "Monitor resource usage during gameplay",
                "Regular backups recommended before configuration changes"
            ]
        }
    
    def validate_server_config(self, config: Dict[str, Any]) -> List[str]:
        return ["ℹ️ Generic validation - check game-specific documentation for detailed config advice"]
    
    def get_performance_recommendations(self, resources: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        cpu_usage = resources.get("cpu_absolute", 0)
        memory_usage = resources.get("memory_bytes", 0)
        memory_limit = resources.get("memory_limit", 1024**3)
        memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
        
        if cpu_usage > 80:
            recommendations.append("🔥 **High CPU Usage**: Consider reducing game settings or player count")
        
        if memory_percent > 85:
            recommendations.append("💾 **High Memory Usage**: Increase RAM allocation or optimize game settings")
        
        if cpu_usage < 50 and memory_percent < 60:
            recommendations.append("✅ **Performance Good**: Resources are well-optimized")
        else:
            recommendations.extend([
                "📊 **Monitor Resources**: Keep track of usage during peak times",
                "🔄 **Regular Restarts**: Consider scheduled restarts to maintain performance",
                "📋 **Game-Specific**: Check documentation for game-specific optimizations"
            ])
        
        return recommendations

# Global knowledge manager instance
knowledge_manager = KnowledgeManager()
```

### ✅ Task 2.2: Smart Diagnostic Tools (Day 3-4)

#### Step 1: Create Advanced Diagnostic Tool
- [ ] **File**: `backend/app/langgraph/tools.py`
- [ ] **Action**: Add smart diagnostic tools (ADD to existing tools)

```python
# ADD THESE IMPORTS TO THE TOP OF YOUR EXISTING tools.py
from ..services.knowledge_manager import knowledge_manager
import json

# ADD THESE NEW TOOLS TO YOUR EXISTING tools.py

@tool
async def diagnose_server_issue(problem_description: str, server_id: str = "auto-detect", session_id: str = "dev_session") -> str:
    """Advanced server diagnostics using game-specific knowledge and real server data"""
    try:
        actual_server_id = await detect_server_id(session_id, server_id)
        
        async with get_user_client(session_id) as client:
            # Get comprehensive server information
            server_details, resources = await asyncio.gather(
                client.get_server_details(actual_server_id),
                client.get_server_resources(actual_server_id)
            )
        
        # Get game-specific advice
        contextual_advice = knowledge_manager.get_contextual_advice(
            server_details, resources, problem_description
        )
        
        # Format comprehensive diagnostic response
        game_info = contextual_advice["game_info"]
        
        response = f"""
🔍 **Advanced Server Diagnostics**

**🎮 Game Detected**: {game_info['name']} ({game_info['category']})
**⚠️ Player Impact Level**: {game_info['player_impact'].upper()}

**📊 Current Server Status**:
- **Status**: {server_details.get('current_state', 'unknown').upper()}
- **CPU**: {resources.get('cpu_absolute', 0):.1f}%
- **Memory**: {resources.get('memory_bytes', 0) / (1024**3):.1f}GB
- **Uptime**: {resources.get('uptime', 0) // 1000 // 60} minutes

**🎯 Issue Analysis**: {problem_description}

**🛠️ Troubleshooting Steps**:
"""
        
        for i, step in enumerate(contextual_advice["troubleshooting_steps"], 1):
            response += f"\n{step}"
        
        response += "\n\n**⚡ Performance Recommendations**:"
        for tip in contextual_advice["performance_tips"]:
            response += f"\n• {tip}"
        
        # Add safety warnings if any
        if contextual_advice["safety_warnings"]:
            response += "\n\n**🚨 Safety Warnings**:"
            for warning in contextual_advice["safety_warnings"]:
                response += f"\n• {warning}"
        
        # Add game-specific features info
        features = []
        if game_info["supports_mods"]:
            features.append("Mods/Plugins")
        if game_info["has_whitelist"]:
            features.append("Whitelist")
        
        if features:
            response += f"\n\n**🎮 Available Features**: {', '.join(features)}"
        
        response += f"\n\n**💡 Focus Area**: {contextual_advice['optimization_focus'].replace('_', ' ').title()}"
        
        return response
        
    except Exception as e:
        return f"❌ **Diagnostic Error**: {str(e)}"

@tool
async def get_server_optimization_report(server_id: str = "auto-detect", session_id: str = "dev_session") -> str:
    """Generate comprehensive server optimization report with game-specific recommendations"""
    try:
        actual_server_id = await detect_server_id(session_id, server_id)
        
        async with get_user_client(session_id) as client:
            server_details, resources = await asyncio.gather(
                client.get_server_details(actual_server_id),
                client.get_server_resources(actual_server_id)
            )
        
        # Detect game and get knowledge module
        game_knowledge = knowledge_manager.get_game_knowledge(server_details)
        game_info = knowledge_manager.game_detector.detect_game(server_details)
        
        # Get optimization recommendations
        perf_recommendations = game_knowledge.get_performance_recommendations(resources)
        
        # Calculate resource efficiency scores
        cpu_usage = resources.get('cpu_absolute', 0)
        memory_usage = resources.get('memory_bytes', 0)
        memory_limit = server_details.get('limits', {}).get('memory', 1024) * 1024 * 1024
        memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
        
        # Generate efficiency scores
        cpu_score = max(0, 100 - cpu_usage) if cpu_usage <= 100 else 0
        memory_score = max(0, 100 - memory_percent) if memory_percent <= 100 else 0
        overall_score = (cpu_score + memory_score) / 2
        
        # Score interpretation
        if overall_score >= 80:
            performance_rating = "🟢 EXCELLENT"
        elif overall_score >= 60:
            performance_rating = "🟡 GOOD" 
        elif overall_score >= 40:
            performance_rating = "🟠 NEEDS ATTENTION"
        else:
            performance_rating = "🔴 CRITICAL"
        
        response = f"""
📈 **Server Optimization Report**

**🎮 Game**: {game_info.name}
**🖥️ Server**: {server_details.get('name', 'Unknown')}
**📊 Overall Performance**: {performance_rating} ({overall_score:.0f}/100)

**📋 Resource Analysis**:
• **CPU Efficiency**: {cpu_score:.0f}/100 (Current: {cpu_usage:.1f}%)
• **Memory Efficiency**: {memory_score:.0f}/100 (Current: {memory_percent:.1f}%)
• **Uptime**: {resources.get('uptime', 0) // 1000 // 3600} hours

**🎯 Optimization Recommendations**:
"""
        
        for recommendation in perf_recommendations:
            response += f"\n• {recommendation}"
        
        # Add game-specific configuration advice
        response += f"\n\n**⚙️ Configuration Focus**: {game_info.optimization_focus.replace('_', ' ').title()}"
        
        # Add next steps
        response += "\n\n**🚀 Next Steps**:"
        if overall_score < 60:
            response += "\n1. **Immediate**: Apply high-priority optimizations listed above"
            response += "\n2. **Monitor**: Check resource usage after changes"
            response += "\n3. **Schedule**: Plan regular optimization reviews"
        else:
            response += "\n1. **Monitor**: Continue monitoring during peak usage times"
            response += "\n2. **Proactive**: Consider optimizations before issues arise"
            response += "\n3. **Plan**: Schedule performance reviews monthly"
        
        response += f"\n\n**📅 Report Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        
        return response
        
    except Exception as e:
        return f"❌ **Report Generation Error**: {str(e)}"

@tool
async def get_game_specific_advice(topic: str, server_id: str = "auto-detect", session_id: str = "dev_session") -> str:
    """Get game-specific advice for configuration, optimization, or troubleshooting"""
    try:
        actual_server_id = await detect_server_id(session_id, server_id)
        
        async with get_user_client(session_id) as client:
            server_details = await client.get_server_details(actual_server_id)
        
        # Get game knowledge
        game_knowledge = knowledge_manager.get_game_knowledge(server_details)
        game_info = knowledge_manager.game_detector.detect_game(server_details)
        
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ["config", "setting", "setup"]):
            # Configuration advice
            scenarios = ["survival_pve", "survival_pvp", "creative", "hardcore"]
            response = f"""
⚙️ **{game_info.name} Configuration Guide**

**Available Scenarios**:
"""
            for scenario in scenarios:
                config_advice = game_knowledge.get_configuration_advice(scenario)
                if config_advice.get("config"):
                    response += f"\n\n**🎮 {scenario.replace('_', ' ').title()} Mode**:"
                    response += "\n```"
                    for key, value in config_advice["config"].items():
                        response += f"\n{key}={value}"
                    response += "\n```"
                    
                    if config_advice.get("performance_tips"):
                        response += "\n**Performance Tips**:"
                        for tip in config_advice["performance_tips"]:
                            response += f"\n• {tip}"
            
        elif any(word in topic_lower for word in ["command", "console", "admin"]):
            # Command suggestions
            if hasattr(game_knowledge, 'get_command_suggestions'):
                commands = game_knowledge.get_command_suggestions(topic)
                response = f"""
📋 **{game_info.name} Console Commands**

**Useful Commands for: {topic}**
"""
                for command in commands:
                    response += f"\n• `{command}`"
                
                response += "\n\n**⚠️ Command Safety**: Always backup before running administrative commands"
            else:
                response = f"📋 **Console Commands**: Check {game_info.name} documentation for specific commands"
        
        elif any(word in topic_lower for word in ["player", "user", "manage"]):
            # Player management advice
            response = f"""
👥 **{game_info.name} Player Management**

**Available Features**:
"""
            if game_info.has_whitelist:
                response += "\n• ✅ **Whitelist**: Supported - use for private servers"
            else:
                response += "\n• ❌ **Whitelist**: Not supported in this game"
            
            if game_info.supports_mods:
                response += "\n• ✅ **Mods/Plugins**: Supported - can add admin tools"
            else:
                response += "\n• ❌ **Mods/Plugins**: Limited or no mod support"
            
            if game_info.has_console_commands:
                response += "\n• ✅ **Console Commands**: Available for player management"
            
            response += f"\n\n**Player Impact Level**: {game_info.player_impact_level.upper()}"
            response += "\n**Recommendation**: " + (
                "Be very careful with player management - changes have high impact" 
                if game_info.player_impact_level == "high" 
                else "Player management changes have moderate impact"
            )
        
        else:
            # General advice
            response = f"""
💡 **General {game_info.name} Advice**

**Game Category**: {game_info.category.value.title()}
**Optimization Focus**: {game_info.optimization_focus.replace('_', ' ').title()}

**Key Features**:
• Mods/Plugins: {'✅ Supported' if game_info.supports_mods else '❌ Not supported'}
• Whitelist: {'✅ Available' if game_info.has_whitelist else '❌ Not available'}
• Console Commands: {'✅ Available' if game_info.has_console_commands else '❌ Limited'}

**Default Ports**: {', '.join(map(str, game_info.default_ports)) if game_info.default_ports else 'Check game documentation'}

**Common Configuration Files**:
"""
            for config_file in game_info.common_configs:
                response += f"\n• {config_file}"
            
            if not game_info.common_configs:
                response += "\n• Check game documentation for configuration files"
        
        return response
        
    except Exception as e:
        return f"❌ **Advice Error**: {str(e)}"

# ADD THESE TO YOUR EXISTING tools list
tools = [
    get_server_status,
    restart_server,
    stop_server,
    start_server,
    send_server_command,
    list_user_servers,
    diagnose_server_issue,           # ADD THIS
    get_server_optimization_report,  # ADD THIS
    get_game_specific_advice,        # ADD THIS
    # ... any other existing tools
]
```

### ✅ Task 2.3: Enhanced Safety and Confirmation System (Day 5)

#### Step 1: Create Safety Manager Service
- [ ] **File**: `backend/app/services/safety_manager.py`
- [ ] **Action**: Create comprehensive safety system

```python
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re

class OperationRisk(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SafetyCheck:
    operation: str
    risk_level: OperationRisk
    warnings: List[str]
    confirmation_required: bool
    prerequisites: List[str]
    impact_description: str

class SafetyManager:
    """
    Manages safety checks and confirmations for server operations
    """
    
    def __init__(self):
        # Define operation risk profiles
        self.operation_risks = {
            "restart": OperationRisk.HIGH,
            "stop": OperationRisk.CRITICAL,
            "kill": OperationRisk.CRITICAL,
            "reinstall": OperationRisk.CRITICAL,
            "delete": OperationRisk.CRITICAL,
            "backup": OperationRisk.LOW,
            "start": OperationRisk.MEDIUM,
            "command": OperationRisk.MEDIUM,
            "config_change": OperationRisk.MEDIUM,
            "file_delete": OperationRisk.HIGH,
            "database_drop": OperationRisk.CRITICAL
        }
        
        # Dangerous command patterns
        self.dangerous_patterns = [
            (r"\b(stop|shutdown|halt)\b", "Server shutdown commands"),
            (r"\b(kill|pkill|killall)\b", "Process termination commands"),
            (r"\b(rm|del|delete)\s+.*", "File deletion commands"),
            (r"\b(drop|truncate)\s+.*", "Database destruction commands"),
            (r"\b(format|fdisk|mkfs)\b", "Disk formatting commands"),
            (r"\b(ban|kick)\s+.*", "Player punishment commands"),
            (r"\bwhitelist\s+(remove|del)\b", "Whitelist removal commands"),
            (r"\b(op|deop)\s+.*", "Permission modification commands")
        ]
    
    def assess_operation_safety(self, operation: str, context: Dict[str, Any] = None) -> SafetyCheck:
        """
        Assess safety of an operation and return safety check result
        """
        operation_lower = operation.lower()
        context = context or {}
        
        # Determine base risk level
        risk_level = OperationRisk.LOW
        for op_pattern, op_risk in self.operation_risks.items():
            if op_pattern in operation_lower:
                risk_level = max(risk_level, op_risk)
                break
        
        warnings = []
        prerequisites = []
        confirmation_required = False
        
        # Check for dangerous patterns in commands
        if "command" in operation_lower:
            command_text = context.get("command", "")
            for pattern, description in self.dangerous_patterns:
                if re.search(pattern, command_text, re.IGNORECASE):
                    warnings.append(f"⚠️ Dangerous command detected: {description}")
                    risk_level = max(risk_level, OperationRisk.HIGH)
        
        # Determine confirmation requirements and warnings based on risk
        if risk_level == OperationRisk.CRITICAL:
            confirmation_required = True
            warnings.extend([
                "🚨 CRITICAL OPERATION - Will have major impact on server",
                "💥 This action may cause data loss or extended downtime",
                "👥 All players will be immediately affected"
            ])
            prerequisites.extend([
                "Ensure all players are notified",
                "Create backup if data could be lost",
                "Verify you have access to restore if needed"
            ])
        
        elif risk_level == OperationRisk.HIGH:
            confirmation_required = True
            warnings.extend([
                "⚠️ HIGH RISK OPERATION - Will disconnect players",
                "⏱️ Server will be temporarily unavailable",
                "📢 Players should be warned in advance"
            ])
            prerequisites.extend([
                "Notify players of upcoming restart/maintenance",
                "Save any unsaved progress if possible"
            ])
        
        elif risk_level == OperationRisk.MEDIUM:
            warnings.append("ℹ️ Moderate impact - May affect player experience")
            if "player" in context.get("target", "").lower():
                confirmation_required = True
        
        # Generate impact description
        impact_descriptions = {
            OperationRisk.CRITICAL: "Will immediately stop server and disconnect all players with potential data loss",
            OperationRisk.HIGH: "Will disconnect all players and require server restart (30-60 seconds downtime)",
            OperationRisk.MEDIUM: "May cause brief interruption or affect specific players",
            OperationRisk.LOW: "Minimal impact on gameplay and players"
        }
        
        impact_description = impact_descriptions.get(risk_level, "Impact level unknown")
        
        return SafetyCheck(
            operation=operation,
            risk_level=risk_level,
            warnings=warnings,
            confirmation_required=confirmation_required,
            prerequisites=prerequisites,
            impact_description=impact_description
        )
    
    def format_safety_warning(self, safety_check: SafetyCheck, context: Dict[str, Any] = None) -> str:
        """
        Format safety check into user-friendly warning message
        """
        context = context or {}
        server_name = context.get("server_name", "Unknown Server")
        current_players = context.get("current_players", "unknown")
        
        # Risk level indicators
        risk_indicators = {
            OperationRisk.CRITICAL: "🚨 CRITICAL OPERATION 🚨",
            OperationRisk.HIGH: "⚠️ HIGH RISK OPERATION ⚠️", 
            OperationRisk.MEDIUM: "⚠️ CAUTION REQUIRED ⚠️",
            OperationRisk.LOW: "ℹ️ LOW RISK OPERATION ℹ️"
        }
        
        warning_msg = f"""
{risk_indicators[safety_check.risk_level]}

**Operation**: {safety_check.operation.title()}
**Server**: {server_name}
**Current Players**: {current_players}

**Impact**: {safety_check.impact_description}
"""
        
        # Add warnings
        if safety_check.warnings:
            warning_msg += "\n**⚠️ Warnings**:"
            for warning in safety_check.warnings:
                warning_msg += f"\n• {warning}"
        
        # Add prerequisites
        if safety_check.prerequisites:
            warning_msg += "\n\n**📋 Prerequisites**:"
            for prereq in safety_check.prerequisites:
                warning_msg += f"\n• {prereq}"
        
        # Add confirmation instruction
        if safety_check.confirmation_required:
            confirmation_phrase = f"{safety_check.operation} with confirmation"
            warning_msg += f"\n\n**To proceed, say**: \"{confirmation_phrase}\""
        
        return warning_msg
    
    def validate_confirmation(self, original_operation: str, confirmation_text: str) -> bool:
        """
        Validate that user properly confirmed the operation
        """
        confirmation_lower = confirmation_text.lower()
        operation_lower = original_operation.lower()
        
        # Check for explicit confirmation phrases
        confirmation_patterns = [
            f"{operation_lower} with confirmation",
            f"{operation_lower} confirmed",
            f"confirm {operation_lower}",
            f"yes {operation_lower}",
            f"proceed with {operation_lower}"
        ]
        
        return any(pattern in confirmation_lower for pattern in confirmation_patterns)
    
    def get_post_operation_advice(self, operation: str, success: bool = True) -> str:
        """
        Get advice for after operation completion
        """
        if not success:
            return """
❌ **Operation Failed**

**Next Steps**:
1. Check server logs for error details
2. Verify server status and connectivity
3. Try alternative approaches if available
4. Contact support if issue persists

**Safety**: Server state may be uncertain - verify before proceeding
"""
        
        operation_lower = operation.lower()
        
        if "restart" in operation_lower:
            return """
✅ **Restart Completed Successfully**

**Next Steps**:
1. **Monitor Status**: Check server comes back online (30-60 seconds)
2. **Verify Functionality**: Test basic server operations
3. **Player Communication**: Notify players server is back online
4. **Log Review**: Check for any startup errors or warnings

**Monitoring**: Use "get server status" to verify everything is working normally
"""
        
        elif "stop" in operation_lower:
            return """
🛑 **Server Stopped Successfully**

**Server is now OFFLINE**

**To restart**:
• Say "start server" when ready to bring back online
• Or use "restart server" to restart in one command

**Important**: Players cannot connect until server is started again
"""
        
        elif "start" in operation_lower:
            return """
🚀 **Server Started Successfully**

**Next Steps**:
1. **Verify Online**: Confirm server shows as "running"
2. **Test Connectivity**: Try connecting with game client
3. **Monitor Resources**: Check CPU/memory usage stabilizes
4. **Player Access**: Server should be ready for player connections

**Monitoring**: Watch for any startup errors in the first few minutes
"""
        
        else:
            return """
✅ **Operation Completed Successfully**

**Recommended**: 
• Monitor server status for any unexpected behavior
• Check logs if any issues arise
• Use "get server status" to verify everything is normal
"""

# Global safety manager instance
safety_manager = SafetyManager()
```

#### Step 2: Integrate Safety System into Tools
- [ ] **File**: `backend/app/langgraph/tools.py`
- [ ] **Action**: Update tools with enhanced safety (MODIFY existing tools)

```python
# ADD THIS IMPORT TO YOUR EXISTING tools.py
from ..services.safety_manager import safety_manager

# REPLACE your existing restart_server tool with this enhanced version
@tool
async def restart_server(server_id: str = "auto-detect", confirm: bool = False, session_id: str = "dev_session") -> str:
    """Restart a game server with comprehensive safety checks"""
    try:
        actual_server_id = await detect_server_id(session_id, server_id)
        
        if not confirm:
            async with get_user_client(session_id) as client:
                server_details, resources = await client.get_server_details(actual_server_id), await client.get_server_resources(actual_server_id)
            
            # Perform safety assessment
            safety_check = safety_manager.assess_operation_safety("restart", {
                "server_name": server_details.get('name', 'Unknown'),
                "current_state": server_details.get('current_state', 'unknown'),
                "uptime_minutes": resources.get('uptime', 0) // 1000 // 60
            })
            
            # Format safety warning
            warning = safety_manager.format_safety_warning(safety_check, {
                "server_name": server_details.get('name', 'Unknown'),
                "current_players": "Check player count" if server_details.get('current_state') == 'running' else "0"
            })
            
            return warning
        
        # Execute restart with safety logging
        async with get_user_client(session_id) as client:
            await client.send_power_action(actual_server_id, "restart")
            
        success_msg = safety_manager.get_post_operation_advice("restart", success=True)
        return success_msg
        
    except Exception as e:
        error_msg = safety_manager.get_post_operation_advice("restart", success=False)
        return f"{error_msg}\n\n**Error Details**: {str(e)}"

# REPLACE your existing stop_server tool with this enhanced version
@tool
async def stop_server(server_id: str = "auto-detect", confirm: bool = False, session_id: str = "dev_session") -> str:
    """Stop a game server with critical safety checks"""
    try:
        actual_server_id = await detect_server_id(session_id, server_id)
        
        if not confirm:
            async with get_user_client(session_id) as client:
                server_details = await client.get_server_details(actual_server_id)
            
            # Critical operation safety assessment
            safety_check = safety_manager.assess_operation_safety("stop", {
                "server_name": server_details.get('name', 'Unknown'),
                "current_state": server_details.get('current_state', 'unknown')
            })
            
            warning = safety_manager.format_safety_warning(safety_check, {
                "server_name": server_details.get('name', 'Unknown'),
                "current_players": "All connected players" if server_details.get('current_state') == 'running' else "0"
            })
            
            return warning
        
        # Execute stop
        async with get_user_client(session_id) as client:
            await client.send_power_action(actual_server_id, "stop")
            
        return safety_manager.get_post_operation_advice("stop", success=True)
        
    except Exception as e:
        error_msg = safety_manager.get_post_operation_advice("stop", success=False)
        return f"{error_msg}\n\n**Error Details**: {str(e)}"

# UPDATE your existing send_server_command tool with enhanced safety
@tool
async def send_server_command(command: str, server_id: str = "auto-detect", session_id: str = "dev_session") -> str:
    """Send console command with intelligent safety analysis"""
    try:
        actual_server_id = await detect_server_id(session_id, server_id)
        
        # Enhanced safety check for commands
        safety_check = safety_manager.assess_operation_safety("command", {
            "command": command,
            "server_id": actual_server_id
        })
        
        # Block dangerous commands unless explicitly confirmed
        if safety_check.risk_level.value in ["high", "critical"]:
            return f"""
{safety_manager.format_safety_warning(safety_check, {"server_name": actual_server_id})}

**Command**: `{command}`

**Safer Alternatives**:
• For player management: Ask me "help with player management"
• For server control: Use "restart/stop/start server" commands
• For configuration: Ask me "help with server settings"

**What are you trying to accomplish?** I can suggest a safer approach.
"""
        
        # Execute safe command
        async with get_user_client(session_id) as client:
            await client.send_console_command(actual_server_id, command)
        
        return f"""
📟 **Console Command Executed**

**Command**: `{command}`
**Status**: ✅ Sent to server console
**Risk Level**: {safety_check.risk_level.value.upper()}

⏳ **Command is processing...**
📊 **Check Results**: Monitor server console or use "get server status"
🎮 **Impact**: {safety_check.impact_description}

{safety_manager.get_post_operation_advice("command", success=True)}
"""
        
    except Exception as e:
        return f"❌ **Command Failed**: {str(e)}"
```

---

## 📦 Week 4: Integration and Testing

### ✅ Task 2.4: Context-Aware Response System (Day 6-7)

#### Step 1: Enhance Agent with Game Context
- [ ] **File**: `backend/app/langgraph/agent.py`
- [ ] **Action**: Update agent to use game knowledge (MODIFY existing call_model function)

```python
# ADD THESE IMPORTS TO YOUR EXISTING agent.py
from ..services.knowledge_manager import knowledge_manager
from ..services.safety_manager import safety_manager

# REPLACE your existing call_model function with this enhanced version
async def call_model(state, config):
    """Enhanced model call with game intelligence and safety awareness"""
    
    # Extract configuration
    system_prompt = config["configurable"].get("system", "")
    frontend_tools = config["configurable"].get("frontend_tools", [])
    user_session = config["configurable"].get("user_session", {})
    
    # Get user's first server for context (if available)
    server_context = {}
    game_context = ""
    
    if user_session.get("accessible_servers"):
        # This would be enhanced to get actual server data
        # For now, we'll use placeholder logic
        server_context = {
            "server_id": user_session["accessible_servers"][0],
            "game_detected": True
        }
        
        # Add game-specific context to system prompt
        game_context = """

GAME INTELLIGENCE ACTIVE:
- Server context automatically detected when possible
- Game-specific troubleshooting and optimization available
- Safety assessments performed for all operations
- Use 'diagnose server issue' for intelligent problem analysis
- Use 'get server optimization report' for performance insights
- Use 'get game specific advice' for configuration help
"""
    
    # Enhanced system prompt with safety and intelligence awareness
    enhanced_system = f"""{system_prompt}

CURRENT USER CONTEXT:
- User ID: {user_session.get('user_id', 'unknown')}
- Available Servers: {len(user_session.get('accessible_servers', []))} servers
- Permissions: {', '.join(user_session.get('user_permissions', []))}
- Session ID: {user_session.get('session_id', 'dev_session')}

SAFETY PROTOCOLS ACTIVE:
- All high-risk operations require explicit confirmation
- Safety assessments performed automatically
- Game-specific impact analysis provided
- Player impact warnings included in all recommendations

INTELLIGENT FEATURES:
- Game detection and contextual advice
- Resource usage analysis and optimization
- Troubleshooting with game-specific knowledge
- Configuration validation and recommendations{game_context}

TOOL USAGE GUIDELINES:
- Always use session_id parameter: "{user_session.get('session_id', 'dev_session')}"
- For server operations, you can use "auto-detect" to use user's first server
- Always explain what operations will do before executing
- Use safety confirmations for potentially disruptive operations
- Leverage intelligent diagnostic tools for complex issues

RESPONSE GUIDELINES:
- Be proactive with safety warnings and confirmations
- Provide game-specific context when available
- Use diagnostic tools to give comprehensive answers
- Suggest optimization opportunities when relevant
- Always prioritize player experience and server stability
"""
    
    messages = [SystemMessage(content=enhanced_system)] + state["messages"]
    model_with_tools = model.bind_tools(get_tool_defs(config))
    response = await model_with_tools.ainvoke(messages)
    
    return {"messages": [response]}
```

### ✅ Task 2.5: Testing and Validation (Day 8-10)

#### Step 1: Create Comprehensive Test Suite
- [ ] **File**: `backend/tests/test_phase2_features.py`
- [ ] **Action**: Create tests for Phase 2 features

```python
import pytest
import asyncio
from app.services.game_detector import GameDetector, GameInfo
from app.services.knowledge_manager import KnowledgeManager
from app.services.safety_manager import SafetyManager, OperationRisk
from app.knowledge.minecraft import MinecraftKnowledgeModule

class TestGameDetection:
    def test_minecraft_detection(self):
        detector = GameDetector()
        
        # Test Minecraft Java detection
        server_info = {
            "egg": {"name": "Minecraft Java Server", "description": "Paper server"},
            "name": "My Minecraft Server"
        }
        
        game_info = detector.detect_game(server_info)
        assert game_info.name == "Minecraft Java Edition"
        assert game_info.supports_mods == True
        assert game_info.has_whitelist == True
    
    def test_rust_detection(self):
        detector = GameDetector()
        
        server_info = {
            "egg": {"name": "Rust Server", "description": "Oxide Rust server"},
            "name": "Rust PvP Server"
        }
        
        game_info = detector.detect_game(server_info)
        assert game_info.name == "Rust"
        assert game_info.category.value == "survival"
    
    def test_unknown_game_fallback(self):
        detector = GameDetector()
        
        server_info = {
            "egg": {"name": "Unknown Game Server", "description": "Custom game"},
            "name": "Custom Server"
        }
        
        game_info = detector.detect_game(server_info)
        assert game_info.name == "Unknown Game"
        assert game_info.category.value == "unknown"

class TestMinecraftKnowledge:
    def test_lag_troubleshooting(self):
        game_info = GameInfo(
            name="Minecraft Java Edition",
            category=None,
            default_ports=[25565],
            common_configs=[],
            optimization_focus="memory_management",
            player_impact_level="high",
            supports_mods=True,
            has_whitelist=True,
            has_console_commands=True
        )
        
        knowledge = MinecraftKnowledgeModule(game_info)
        steps = knowledge.get_troubleshooting_steps("server lag issues")
        
        assert len(steps) > 0
        assert any("tps" in step.lower() for step in steps)
        assert any("view distance" in step.lower() for step in steps)
    
    def test_configuration_scenarios(self):
        game_info = GameInfo(
            name="Minecraft Java Edition",
            category=None,
            default_ports=[25565],
            common_configs=[],
            optimization_focus="memory_management",
            player_impact_level="high",
            supports_mods=True,
            has_whitelist=True,
            has_console_commands=True
        )
        
        knowledge = MinecraftKnowledgeModule(game_info)
        
        # Test PvP configuration
        pvp_config = knowledge.get_configuration_advice("survival_pvp")
        assert pvp_config["config"]["pvp"] == "true"
        assert pvp_config["config"]["difficulty"] == "hard"
        
        # Test Creative configuration
        creative_config = knowledge.get_configuration_advice("creative")
        assert creative_config["config"]["gamemode"] == "creative"
        assert creative_config["config"]["difficulty"] == "peaceful"

class TestSafetyManager:
    def test_restart_safety_assessment(self):
        safety_manager = SafetyManager()
        
        safety_check = safety_manager.assess_operation_safety("restart")
        assert safety_check.risk_level == OperationRisk.HIGH
        assert safety_check.confirmation_required == True
        assert len(safety_check.warnings) > 0
    
    def test_dangerous_command_detection(self):
        safety_manager = SafetyManager()
        
        safety_check = safety_manager.assess_operation_safety("command", {
            "command": "stop server now"
        })
        
        assert safety_check.risk_level.value in ["high", "critical"]
        assert any("dangerous" in warning.lower() for warning in safety_check.warnings)
    
    def test_confirmation_validation(self):
        safety_manager = SafetyManager()
        
        # Valid confirmations
        assert safety_manager.validate_confirmation("restart", "restart with confirmation") == True
        assert safety_manager.validate_confirmation("stop", "confirm stop server") == True
        
        # Invalid confirmations
        assert safety_manager.validate_confirmation("restart", "maybe restart") == False
        assert safety_manager.validate_confirmation("stop", "just stop") == False

# Integration test
class TestKnowledgeIntegration:
    def test_contextual_advice_generation(self):
        knowledge_manager = KnowledgeManager()
        
        server_info = {
            "egg": {"name": "Minecraft Java Server"},
            "name": "Test Server"
        }
        
        resources = {
            "cpu_absolute": 85.0,
            "memory_bytes": 3 * 1024**3,  # 3GB
            "memory_limit": 4 * 1024**3   # 4GB
        }
        
        advice = knowledge_manager.get_contextual_advice(
            server_info, resources, "server is running slowly"
        )
        
        assert advice["game_info"]["name"] == "Minecraft Java Edition"
        assert len(advice["troubleshooting_steps"]) > 0
        assert len(advice["performance_tips"]) > 0
        assert "memory_management" in advice["optimization_focus"]

if __name__ == "__main__":
    pytest.main([__file__])
```

#### Step 2: Manual Testing Scenarios
- [ ] **Test Game Detection**:
  - [ ] Create servers with different game types in test environment
  - [ ] Verify detection accuracy for Minecraft, Rust, ARK, etc.
  - [ ] Test fallback to generic knowledge for unknown games

- [ ] **Test Smart Diagnostics**:
  - [ ] "My Minecraft server is lagging" → Should provide MC-specific steps
  - [ ] "Rust server keeps crashing" → Should provide Rust-specific advice
  - [ ] "diagnose server issue lag problems" → Should use advanced diagnostics

- [ ] **Test Safety System**:
  - [ ] "restart server" → Should show safety warning with confirmation
  - [ ] "send dangerous command" → Should block with safer alternatives
  - [ ] "restart server with confirmation" → Should execute after warning

- [ ] **Test Optimization Reports**:
  - [ ] "get server optimization report" → Should show game-specific recommendations
  - [ ] Test with high CPU/memory usage scenarios
  - [ ] Verify performance scoring system works

#### Step 3: Performance Testing
- [ ] **Load Testing Enhanced Features**:
  - [ ] Test game detection under concurrent requests
  - [ ] Verify knowledge module caching works properly
  - [ ] Test safety assessments don't slow down responses significantly

- [ ] **Memory Usage Testing**:
  - [ ] Monitor memory usage with multiple knowledge modules loaded
  - [ ] Test knowledge cache cleanup and limits
  - [ ] Verify no memory leaks in game detection

---

## 🎯 Phase 2 Success Criteria

### Functional Testing Checklist
- [ ] **Game Intelligence**:
  - [ ] Automatically detects top 10 game types correctly
  - [ ] Provides game-specific troubleshooting steps
  - [ ] Offers relevant configuration advice for different scenarios
  - [ ] Game-specific performance recommendations work

- [ ] **Smart Diagnostics**:
  - [ ] Advanced diagnostic tool combines server data + game knowledge
  - [ ] Optimization reports provide actionable recommendations
  - [ ] Contextual advice adapts to detected game type
  - [ ] Performance scoring system works accurately

- [ ] **Enhanced Safety**:
  - [ ] All high-risk operations require proper confirmation
  - [ ] Dangerous commands are detected and blocked safely
  - [ ] Safety warnings are clear and informative
  - [ ] Post-operation advice helps users monitor results

- [ ] **Context Awareness**:
  - [ ] Agent responses include game-specific context
  - [ ] Server resource analysis considers game type
  - [ ] Recommendations adapt to detected game characteristics
  - [ ] Safety assessments consider game-specific player impact

### Performance Benchmarks
- [ ] **Response Times**:
  - [ ] Game detection: < 100ms
  - [ ] Smart diagnostics: < 3 seconds
  - [ ] Optimization reports: < 5 seconds
  - [ ] Safety assessments: < 200ms

- [ ] **Accuracy Targets**:
  - [ ] Game detection: > 95% for supported games
  - [ ] Troubleshooting relevance: User satisfaction > 80%
  - [ ] Safety warning accuracy: 100% for dangerous operations
  - [ ] Performance recommendations: Measurable improvements

### User Experience Goals
- [ ] **Intelligence**:
  - [ ] Users notice more relevant, specific advice
  - [ ] Troubleshooting steps are actionable and effective
  - [ ] Configuration advice matches their game type
  - [ ] Performance recommendations yield actual improvements

- [ ] **Safety**:
  - [ ] Users feel confident about server operations
  - [ ] No accidental destructive operations
  - [ ] Clear understanding of operation impacts
  - [ ] Proper warnings prevent player disruption

---

## 🚀 Ready for Phase 3

After Phase 2 completion, you'll have:
- ✅ Intelligent game detection for 10+ popular games
- ✅ Game-specific knowledge modules with contextual advice
- ✅ Smart diagnostic tools combining real data + game intelligence
- ✅ Enhanced safety system with risk assessment
- ✅ Context-aware responses that adapt to detected game type
- ✅ Performance optimization recommendations based on game characteristics

**Next**: Phase 3 will add advanced file operations, backup management, database tools, and multi-server management capabilities.