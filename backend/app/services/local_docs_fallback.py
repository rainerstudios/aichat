import os
import re
import asyncio
from typing import Dict, List, Optional
from pathlib import Path

class LocalDocsFallback:
    """
    Fallback service that searches local documentation files when AutoRAG is slow/unavailable
    """
    
    def __init__(self):
        self.docs_path = Path(__file__).parent.parent / "crawled_docs"
        self.docs_cache = {}
        
    async def search_local_docs(self, query: str, game_type: str = None) -> Optional[str]:
        """
        Search local documentation files for relevant information
        """
        try:
            query_lower = query.lower()
            
            # Game-specific file mapping
            game_files = {
                "arma reforger": ["arma_reforger_server_setup.md"],
                "minecraft": ["minecraft_server_setup_guide.md", "paper_server_setup.md", "spigot_installation_guide.md"],
                "counter-strike": ["cs2_dedicated_servers.md"],
                "pterodactyl": ["pterodactyl_panel_main.md", "pterodactyl_panel_installation.md", "pterodactyl_wings.md"],
                "rust": ["rust_server_setup.md"]
            }
            
            # Determine relevant files to search
            files_to_search = []
            
            # First try game_type specific files
            if game_type:
                game_key = game_type.lower().replace("(", "").replace(")", "")
                for key, files in game_files.items():
                    if key in game_key or any(word in game_key for word in key.split()):
                        files_to_search.extend(files)
            
            # Also search based on query content
            for key, files in game_files.items():
                if key in query_lower or any(word in query_lower for word in key.split()):
                    files_to_search.extend(files)
            
            # Remove duplicates
            files_to_search = list(set(files_to_search))
            
            # If no specific files found, search all files
            if not files_to_search:
                files_to_search = [f for f in os.listdir(self.docs_path) if f.endswith('.md')]
            
            # Search through files
            results = []
            for filename in files_to_search:
                file_path = self.docs_path / filename
                if file_path.exists():
                    content = await self._search_file(file_path, query_lower)
                    if content:
                        results.append({
                            "file": filename,
                            "content": content
                        })
            
            if results:
                return self._format_results(results, query)
            
            return None
            
        except Exception as e:
            print(f"Local docs fallback error: {e}")
            return None
    
    async def _search_file(self, file_path: Path, query: str) -> Optional[str]:
        """Search within a single file for relevant content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple keyword matching
            query_words = query.replace("server", "").replace("setup", "").split()
            query_words = [word for word in query_words if len(word) > 2]  # Filter short words
            
            if not query_words:
                query_words = ["server", "setup", "configuration"]
            
            # Find paragraphs containing query words
            paragraphs = content.split('\n\n')
            relevant_paragraphs = []
            
            for paragraph in paragraphs:
                paragraph_lower = paragraph.lower()
                if any(word in paragraph_lower for word in query_words):
                    # Clean up the paragraph
                    clean_paragraph = paragraph.strip()
                    if clean_paragraph and len(clean_paragraph) > 50:  # Skip very short paragraphs
                        relevant_paragraphs.append(clean_paragraph)
            
            if relevant_paragraphs:
                # Return first few relevant paragraphs
                return '\n\n'.join(relevant_paragraphs[:3])
            
            return None
            
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def _format_results(self, results: List[Dict], query: str) -> str:
        """Format search results into a readable response"""
        if not results:
            return None
        
        response = f"Based on the local documentation, here's information about {query}:\n\n"
        
        for result in results[:2]:  # Limit to top 2 results
            filename = result["file"].replace("_", " ").replace(".md", "").title()
            content = result["content"]
            
            # Truncate if too long
            if len(content) > 800:
                content = content[:800] + "..."
            
            response += f"**{filename}:**\n{content}\n\n"
        
        response += "*[Retrieved from local documentation due to slow documentation service]*"
        
        return response

# Global instance
_local_docs_fallback = None

def get_local_docs_fallback() -> LocalDocsFallback:
    """Get or create global local docs fallback instance"""
    global _local_docs_fallback
    if _local_docs_fallback is None:
        _local_docs_fallback = LocalDocsFallback()
    return _local_docs_fallback