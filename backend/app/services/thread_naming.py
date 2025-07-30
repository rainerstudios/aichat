"""
Intelligent thread naming service
Generates meaningful titles from user messages
"""

import re
from typing import List, Dict, Any

class ThreadNamingService:
    """Service for generating intelligent thread titles"""
    
    # Gaming server related keywords for context-aware naming
    GAMING_KEYWORDS = {
        'server': ['server', 'servers', 'hosting', 'host'],
        'performance': ['performance', 'lag', 'fps', 'slow', 'speed', 'optimize'],
        'setup': ['setup', 'install', 'configure', 'config', 'installation'],
        'mods': ['mod', 'mods', 'plugin', 'plugins', 'addon', 'addons'],
        'error': ['error', 'issue', 'problem', 'broken', 'fix', 'help', 'trouble'],
        'minecraft': ['minecraft', 'paper', 'spigot', 'bukkit', 'forge'],
        'rust': ['rust', 'oxide', 'umod'],
        'cs2': ['cs2', 'counter-strike', 'source'],
        'arma': ['arma', 'reforger'],
        'pterodactyl': ['pterodactyl', 'panel', 'wing', 'wings'],
        'network': ['port', 'ports', 'firewall', 'connection', 'connect'],
        'storage': ['storage', 'disk', 'space', 'backup', 'file', 'files']
    }
    
    # Common question patterns
    QUESTION_PATTERNS = [
        (r'\bhow\s+(?:do\s+i|to|can\s+i)\s+(.{1,35})', 'How to {}'),
        (r'\bwhat\s+(?:is|are)\s+(.{1,35})', 'What {}'),
        (r'\bwhy\s+(?:is|are|does|doesn\'t)\s+(.{1,35})', 'Why {}'),
        (r'\bwhere\s+(?:is|are|do|can)\s+(.{1,35})', 'Where {}'),
        (r'\bwhen\s+(?:should|do|does)\s+(.{1,35})', 'When {}'),
        (r'\bcan\s+(?:i|you)\s+(.{1,35})', 'Can {}'),
        (r'\bwould\s+(.{1,35})', 'Would {}'),
        (r'\bshould\s+(.{1,35})', 'Should {}'),
    ]
    
    @classmethod
    def generate_title(cls, message_content: List[Dict[str, Any]], max_length: int = 50) -> str:
        """
        Generate a meaningful title from message content
        
        Args:
            message_content: Assistant-UI format message content
            max_length: Maximum title length
            
        Returns:
            Generated title string
        """
        # Extract text from Assistant-UI format
        text = cls._extract_text_content(message_content)
        
        if not text:
            return "New Chat"
        
        # Clean and normalize text
        text = cls._clean_text(text)
        
        # Try different title generation strategies
        title = (
            cls._extract_question_pattern(text) or
            cls._extract_with_gaming_context(text) or
            cls._extract_key_phrase(text) or
            cls._truncate_cleanly(text, max_length)
        )
        
        # Final cleanup and length check
        title = cls._finalize_title(title, max_length)
        
        return title if title and len(title.strip()) > 3 else "New Chat"
    
    @classmethod
    def _extract_text_content(cls, message_content: List[Dict[str, Any]]) -> str:
        """Extract text from Assistant-UI message format"""
        text_parts = []
        
        for part in message_content:
            if isinstance(part, dict) and part.get('type') == 'text':
                text_parts.append(part.get('text', ''))
        
        return ' '.join(text_parts).strip()
    
    @classmethod
    def _clean_text(cls, text: str) -> str:
        """Clean and normalize text for processing"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common filler words at the start
        text = re.sub(r'^(hi|hello|hey|yo)\s*,?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^(i\s+)?(need|want|would\s+like)\s+(help\s+)?(with\s+)?', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    @classmethod
    def _extract_question_pattern(cls, text: str) -> str:
        """Extract title from common question patterns"""
        for pattern, template in cls.QUESTION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                captured = match.group(1).strip()
                # Remove trailing punctuation and clean up
                captured = re.sub(r'[.!?]+$', '', captured).strip()
                if captured:
                    title = template.format(captured)
                    return cls._truncate_cleanly(title, 45)
        
        return None
    
    @classmethod
    def _extract_with_gaming_context(cls, text: str) -> str:
        """Extract title with gaming server context"""
        text_lower = text.lower()
        
        # Find relevant gaming categories
        found_categories = []
        for category, keywords in cls.GAMING_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                found_categories.append(category)
        
        if found_categories:
            # Try to extract a meaningful phrase around gaming keywords
            for category in found_categories[:2]:  # Use top 2 categories
                for keyword in cls.GAMING_KEYWORDS[category]:
                    if keyword in text_lower:
                        # Find context around the keyword
                        pattern = rf'(.{{0,15}}\b{re.escape(keyword)}\b.{{0,25}})'
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            context = match.group(1).strip()
                            context = re.sub(r'^(my|the|a|an)\s+', '', context, flags=re.IGNORECASE)
                            if context:
                                return cls._truncate_cleanly(context.title(), 45)
        
        return None
    
    @classmethod
    def _extract_key_phrase(cls, text: str) -> str:
        """Extract a key phrase from the text"""
        # Look for phrases after common starters
        patterns = [
            r'(?:issue|problem|trouble)\s+with\s+(.{1,30})',
            r'(?:setting\s+up|installing)\s+(.{1,30})',
            r'(?:configure|configuring)\s+(.{1,30})',
            r'(?:error|errors)\s+(?:with|in|on)\s+(.{1,30})',
            r'(.{1,30})\s+(?:not\s+working|isn\'t\s+working|doesn\'t\s+work)',
            r'(.{1,30})\s+(?:crashing|crashed)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                phrase = match.group(1).strip()
                phrase = re.sub(r'[.!?]+$', '', phrase).strip()
                if phrase:
                    return cls._truncate_cleanly(phrase.title(), 40)
        
        return None
    
    @classmethod
    def _truncate_cleanly(cls, text: str, max_length: int) -> str:
        """Truncate text cleanly at word boundaries"""
        if len(text) <= max_length:
            return text
        
        # Find the last space before max_length
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.7:  # Don't truncate too aggressively
            return truncated[:last_space].strip()
        else:
            return truncated.strip() + '...'
    
    @classmethod
    def _finalize_title(cls, title: str, max_length: int) -> str:
        """Final cleanup and validation of title"""
        if not title:
            return "New Chat"
        
        # Capitalize first letter
        title = title[0].upper() + title[1:] if len(title) > 1 else title.upper()
        
        # Remove trailing punctuation except question marks
        title = re.sub(r'[.!,;:]+$', '', title)
        
        # Ensure it's not too long
        if len(title) > max_length:
            title = cls._truncate_cleanly(title, max_length)
        
        return title

# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_messages = [
        [{"type": "text", "text": "How do I install Minecraft mods on my server?"}],
        [{"type": "text", "text": "My Rust server keeps crashing"}],
        [{"type": "text", "text": "Help with Pterodactyl panel configuration"}],
        [{"type": "text", "text": "What ports do I need to open for CS2?"}],
        [{"type": "text", "text": "Performance issues with Arma Reforger server"}],
        [{"type": "text", "text": "Hi, I need help setting up backups"}],
    ]
    
    for msg in test_messages:
        title = ThreadNamingService.generate_title(msg)
        print(f"Message: {msg[0]['text']}")
        print(f"Title: {title}")
        print()