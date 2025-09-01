"""Comic book script parser module."""

import re
from pathlib import Path
from typing import List, Optional, Tuple

from src.models import (
    Caption,
    ComicScript,
    Dialogue,
    Page,
    Panel,
    PanelType,
    SoundEffect,
)


class ScriptParser:
    """Parser for industry-standard comic book scripts."""
    
    def __init__(self):
        """Initialize the script parser."""
        self.current_page = None
        self.current_panel = None
        self.script = None
        
    def parse_script(self, script_path: str) -> ComicScript:
        """Parse a comic book script from file.
        
        Args:
            script_path: Path to the script file
            
        Returns:
            Parsed ComicScript object
        """
        path = Path(script_path)
        if not path.exists():
            raise FileNotFoundError(f"Script file not found: {script_path}")
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> ComicScript:
        """Parse comic script from text content.
        
        Args:
            content: Script text content
            
        Returns:
            Parsed ComicScript object
        """
        lines = content.strip().split('\n')
        self.script = ComicScript()
        
        # Parse title if present
        if lines and lines[0].startswith('Title:'):
            self.script.title = lines[0].replace('Title:', '').strip()
            lines = lines[1:]
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
                
            # Check for page marker
            if self._is_page_marker(line):
                page_num, panel_count = self._parse_page_marker(line)
                self._start_new_page(page_num)
                i += 1
                continue
                
            # Check for panel marker
            if self._is_panel_marker(line):
                panel_num = self._parse_panel_marker(line)
                self._start_new_panel(panel_num)
                i += 1
                continue
                
            # Parse panel content
            if self.current_panel:
                # Check for panel description (first line after panel marker)
                if self.current_panel.description == "[pending]" and not self._is_dialogue(line) and not self._is_caption(line) and not self._is_sfx(line):
                    # Collect multi-line description
                    description_lines = [line]
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if not next_line or self._is_dialogue(next_line) or self._is_caption(next_line) or self._is_sfx(next_line) or self._is_panel_marker(next_line) or self._is_page_marker(next_line):
                            break
                        description_lines.append(next_line)
                        j += 1
                    self.current_panel.description = ' '.join(description_lines)
                    i = j
                    continue
                    
                # Parse dialogue
                if self._is_dialogue(line):
                    character, text, is_thought = self._parse_dialogue(line)
                    emotion = "thoughtful" if is_thought else None
                    self.current_panel.add_dialogue(character, text, emotion)
                    i += 1
                    continue
                    
                # Parse caption
                if self._is_caption(line):
                    caption_text, caption_type = self._parse_caption(line)
                    self.current_panel.add_caption(caption_text, "top", caption_type)
                    i += 1
                    continue
                    
                # Parse sound effect
                if self._is_sfx(line):
                    sfx_text = self._parse_sfx(line)
                    self.current_panel.add_sound_effect(sfx_text)
                    i += 1
                    continue
                    
            i += 1
        
        # Add final panel if exists and has content
        if self.current_panel and self.current_panel.description != "[pending]":
            if self.current_page:
                self.current_page.add_panel(self.current_panel)
        
        # Add final page if exists
        if self.current_page and self.current_page.panels:
            self.script.add_page(self.current_page)
            
        return self.script
    
    def _is_page_marker(self, line: str) -> bool:
        """Check if line is a page marker."""
        return bool(re.match(r'^PAGE\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|\d+)', line.upper()))
    
    def _parse_page_marker(self, line: str) -> Tuple[int, Optional[int]]:
        """Parse page number and optional panel count from page marker."""
        # Convert word numbers to integers
        word_to_num = {
            'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 
            'FIVE': 5, 'SIX': 6, 'SEVEN': 7, 'EIGHT': 8,
            'NINE': 9, 'TEN': 10
        }
        
        match = re.match(r'^PAGE\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|\d+)(?:\s*\((\d+)\s*PANELS?\))?', line.upper())
        if match:
            page_part = match.group(1)
            panel_count = int(match.group(2)) if match.group(2) else None
            
            if page_part in word_to_num:
                page_num = word_to_num[page_part]
            else:
                page_num = int(page_part)
                
            return page_num, panel_count
        return 1, None
    
    def _is_panel_marker(self, line: str) -> bool:
        """Check if line is a panel marker."""
        return bool(re.match(r'^Panel\s+\d+', line, re.IGNORECASE))
    
    def _parse_panel_marker(self, line: str) -> int:
        """Parse panel number from panel marker."""
        match = re.match(r'^Panel\s+(\d+)', line, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 1
    
    def _is_dialogue(self, line: str) -> bool:
        """Check if line is dialogue."""
        # Match patterns like "CHARACTER (balloon):" or "CHARACTER (thought):"
        return bool(re.match(r'^[A-Z][A-Z\s]+\s*\((balloon|thought|whisper|shout)\)\s*:', line))
    
    def _parse_dialogue(self, line: str) -> Tuple[str, str, bool]:
        """Parse dialogue line into character, text, and whether it's a thought."""
        match = re.match(r'^([A-Z][A-Z\s]+)\s*\((balloon|thought|whisper|shout)\)\s*:\s*(.+)', line)
        if match:
            character = match.group(1).strip()
            dialogue_type = match.group(2)
            text = match.group(3).strip()
            is_thought = dialogue_type == "thought"
            return character, text, is_thought
        return "", "", False
    
    def _is_caption(self, line: str) -> bool:
        """Check if line is a caption."""
        return line.startswith('CAPTION')
    
    def _parse_caption(self, line: str) -> Tuple[str, str]:
        """Parse caption line into text and type."""
        # Match patterns like "CAPTION (NARRATION):" or just "CAPTION:"
        match = re.match(r'^CAPTION(?:\s*\(([^)]+)\))?\s*:\s*(.+)', line)
        if match:
            caption_type = match.group(1).lower() if match.group(1) else "narration"
            text = match.group(2).strip()
            return text, caption_type
        return line.replace('CAPTION:', '').strip(), "narration"
    
    def _is_sfx(self, line: str) -> bool:
        """Check if line is a sound effect."""
        return line.startswith('SFX:')
    
    def _parse_sfx(self, line: str) -> str:
        """Parse sound effect text."""
        return line.replace('SFX:', '').strip()
    
    def _start_new_page(self, page_num: int):
        """Start a new page in the script."""
        # Add current panel if it exists and has content
        if self.current_panel and self.current_panel.description != "[pending]":
            if self.current_page:
                self.current_page.add_panel(self.current_panel)
        
        # Add current page if it exists
        if self.current_page and self.current_page.panels:
            self.script.add_page(self.current_page)
            
        self.current_page = Page(number=page_num)
        self.current_panel = None
    
    def _start_new_panel(self, panel_num: int):
        """Start a new panel in the current page."""
        if not self.current_page:
            # Create default page if none exists
            self.current_page = Page(number=1)
            
        # Add current panel if it exists
        if self.current_panel and self.current_panel.description != "[pending]":
            self.current_page.add_panel(self.current_panel)
            
        # Create panel with placeholder description that will be updated
        self.current_panel = Panel(number=panel_num, description="[pending]")
        
        # Determine panel type based on description (will be set later)
        # This is a placeholder that will be updated when description is parsed
    
    def _determine_panel_type(self, description: str) -> PanelType:
        """Determine panel type from description keywords."""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['wide shot', 'wide panel', 'establishing']):
            return PanelType.WIDE
        elif any(word in description_lower for word in ['close-up', 'close up', 'tight shot', 'close on']):
            return PanelType.CLOSE_UP
        elif any(word in description_lower for word in ['splash', 'full page']):
            return PanelType.SPLASH
        else:
            return PanelType.MEDIUM