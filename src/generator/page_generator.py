"""Page generator for creating complete comic pages in a single pass."""

import logging
from typing import List, Optional, Dict, Any
from PIL import Image
from io import BytesIO

from src.models import Page, Panel

logger = logging.getLogger(__name__)


class PageGenerator:
    """Generates complete comic pages in a single API call."""
    
    def __init__(self, gemini_client, debug_dir=None):
        """Initialize page generator.
        
        Args:
            gemini_client: Gemini API client
            debug_dir: Optional directory for saving debug information
        """
        self.client = gemini_client
        self.page_width = 2400
        self.page_height = 3600
        self.debug_dir = debug_dir
        
    async def generate_page(
        self,
        page: Page,
        previous_pages: Optional[List[Image.Image]] = None,
        style_context: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Generate a complete comic page with all panels.
        
        Args:
            page: Page object containing panels to generate
            previous_pages: Previous page images for context (PIL Images)
            style_context: Style configuration
            
        Returns:
            Complete page image as bytes
        """
        import time
        start_time = time.time()
        
        try:
            # Build comprehensive page prompt
            prompt = self._build_page_prompt(page, len(previous_pages) if previous_pages else 0)
            
            # Log prompt for debugging
            logger.info(f"Generating page {page.number} with {len(page.panels)} panels")
            logger.debug(f"Page prompt:\n{prompt}")
            
            # Save prompt to debug directory if specified
            if self.debug_dir:
                self._save_debug_prompt(page.number, prompt)
            
            # Prepare previous pages as context
            # Limit to last 3 pages to avoid token limits while maintaining good consistency
            max_context_pages = 3
            if previous_pages:
                context_images = previous_pages[-max_context_pages:]
                logger.info(f"Using last {len(context_images)} page(s) as context")
            else:
                context_images = []
            
            # Call Gemini with prompt and context
            page_image_bytes = await self.client.generate_page_image(
                prompt=prompt,
                context_images=context_images,
                style_config=style_context
            )
            
            generation_time = time.time() - start_time
            logger.info(f"Page {page.number} generated in {generation_time:.2f}s")
            
            return page_image_bytes
            
        except Exception as e:
            logger.error(f"Error generating page {page.number}: {e}")
            raise
    
    def _build_page_prompt(self, page: Page, num_previous_pages: int = 0) -> str:
        """Build detailed prompt for entire page generation.
        
        Args:
            page: Page object with panels
            num_previous_pages: Number of previous pages provided as context
            
        Returns:
            Detailed prompt string
        """
        num_panels = len(page.panels)
        
        # Add context about previous pages if provided
        context_info = ""
        if num_previous_pages > 0:
            context_info = f"""
CONTEXT: You have been provided with {num_previous_pages} previous page(s) of this comic as reference images.
- Maintain EXACT consistency with the art style, colors, and character designs from the previous pages
- Continue the story naturally from where the previous page(s) left off
- Keep the same visual tone and panel layout style

"""
        
        prompt = f"""{context_info}Generate a complete comic book page with EXACTLY {num_panels} panels.

PAGE SPECIFICATIONS:
- Dimensions: EXACTLY 2400x3600 pixels
- Layout: {self._get_layout_description(num_panels)}
- Margins: 15px around the entire page
- Panel gutters: 5px between panels
- All panels must be EXACTLY the same size
- Black panel borders (2px width)

PANEL CONTENT:
{self._build_panels_description(page.panels)}

CRITICAL TEXT REQUIREMENTS - READ CAREFULLY:
⚠️  EVERY SINGLE WORD IN QUOTES MUST BE COMPLETE AND READABLE ⚠️
⚠️  DO NOT TRUNCATE, ABBREVIATE, OR OMIT ANY WORDS ⚠️
⚠️  ENSURE ALL WORDS IN QUOTES ARE COMPLETE ⚠️

CRITICAL REQUIREMENTS:
1. Generate the ENTIRE page as a single 2400x3600px image
2. All {num_panels} panels must be clearly separated with black borders
3. Each panel must contain its specified content EXACTLY as described
4. ALL TEXT IN DOUBLE QUOTES MUST APPEAR EXACTLY AS WRITTEN IN THE IMAGE - NO MISSING WORDS
5. VERIFY EACH QUOTED TEXT IS COMPLETE BEFORE FINISHING THE IMAGE
6. ALL text (captions, dialogue, sound effects) must be INSIDE panel boundaries
7. Captions (text after "Caption:") should be in yellow/white rectangular boxes at top or bottom of panels
8. Character dialogue (text after character names) should be in white speech bubbles with tails pointing to speakers
9. CRITICAL: Speech bubble size must match text length - longer text requires larger bubbles
10. For short text (1-4 words): Use compact speech bubbles
11. For medium text (5-8 words): Use standard-sized speech bubbles with adequate padding
12. For long text (9+ words): Use large, spacious speech bubbles with multiple lines if needed
13. Thought bubbles (marked with "Thought Bubble") should be cloud-shaped with appropriate sizing
14. Sound effects (text after "SFX:") should be stylized text integrated into the artwork
15. Maintain consistent art style across all panels
16. Maintain consistent character appearances across all panels
17. The page should read naturally from top-left to bottom-right
18. DOUBLE-CHECK: All quoted text must be rendered COMPLETELY with NO missing words

STYLE REQUIREMENTS:
- Professional comic book art style
- Clear, readable text in appropriate bubbles/boxes
- Consistent color palette throughout the page
- Dynamic and engaging visual composition

⚠️ FINAL TEXT VERIFICATION CHECKLIST ⚠️
Before completing the image, verify:
1. Every quoted dialogue is complete with ALL words present
2. Every quoted caption is complete with ALL words present  
3. Every quoted sound effect is complete with ALL words present
4. No text has been truncated, abbreviated, or cut off
5. All speech bubbles contain the full intended text

OUTPUT: One complete comic page image of EXACTLY 2400x3600 pixels containing all {num_panels} panels arranged in the specified layout with ALL TEXT RENDERED COMPLETELY."""
        
        return prompt
    
    def _get_layout_description(self, num_panels: int) -> str:
        """Get layout description for number of panels.
        
        Args:
            num_panels: Number of panels on the page
            
        Returns:
            Layout description string
        """
        layouts = {
            1: "Single full-page panel filling the entire page",
            2: "Two panels stacked vertically (1x2 grid) of equal size",
            3: "Three panels stacked vertically (1x3 grid) of equal size", 
            4: "Four panels in a 2x2 grid, all exactly the same size",
            5: "Five panels: 2 equal-sized panels on top row, 3 equal-sized panels on bottom row",
            6: "Six panels in a 2x3 grid (2 columns, 3 rows), all exactly the same size",
            7: "Seven panels: 3 panels top row, 3 panels middle row, 1 full-width panel bottom",
            8: "Eight panels in a 2x4 grid, all exactly the same size",
            9: "Nine panels in a 3x3 grid, all exactly the same size",
            10: "Ten panels in a 2x5 grid, all exactly the same size",
            11: "Eleven panels: 3x3 grid plus 2 panels at bottom",
            12: "Twelve panels in a 3x4 grid, all exactly the same size"
        }
        return layouts.get(num_panels, f"{num_panels} panels in an appropriate grid layout with all panels the same size")
    
    def _build_panels_description(self, panels: List[Panel]) -> str:
        """Build detailed description of all panels.
        
        Args:
            panels: List of Panel objects
            
        Returns:
            Combined panel descriptions
        """
        descriptions = []
        
        for i, panel in enumerate(panels, 1):
            # Use raw_text if available, otherwise use description
            content = getattr(panel, 'raw_text', panel.description)
            
            # Process the content to add quotes around text elements
            processed_content = self._add_quotes_to_text(content)
            
            panel_desc = f"""
PANEL {i} (Position: {self._get_panel_position(i, len(panels))}):
{processed_content}

Visual requirements for Panel {i}:
- This panel must be clearly separated from other panels with a black border
- All dialogue, captions, and sound effects must be INSIDE this panel's boundaries
- ⚠️ ALL TEXT IN QUOTES MUST APPEAR EXACTLY AS WRITTEN - NO MISSING WORDS ⚠️
- CRITICAL: Every single word in quotes must be complete and readable
- Check that all quoted text is rendered completely before finalizing this panel
- Maintain character consistency with previous panels
- Follow standard comic book panel composition"""
            
            descriptions.append(panel_desc.strip())
        
        return "\n\n".join(descriptions)
    
    def _add_quotes_to_text(self, content: str) -> str:
        """Add quotes around text elements that should appear in the image.
        Also breaks down longer sentences for better text rendering.
        
        Args:
            content: Panel content text
            
        Returns:
            Content with quoted text elements and optimized for complete text rendering
        """
        import re
        
        lines = content.split('\n')
        processed_lines = []
        
        for line in lines:
            # Handle Caption: lines
            if line.startswith('Caption:'):
                text = line[8:].strip()
                word_count = len(text.split())
                caption_instruction = self._get_caption_size_instruction(word_count)
                
                # Break down longer captions
                if len(text) > 40:
                    # Try to split at natural break points
                    if '...' in text:
                        parts = text.split('...', 1)
                        part1_words = len(parts[0].strip().split())
                        part1_instruction = self._get_caption_size_instruction(part1_words)
                        processed_lines.append(f'Caption: "{parts[0].strip()}..." {part1_instruction}')
                        if parts[1].strip():
                            part2_words = len(parts[1].strip().split())
                            part2_instruction = self._get_caption_size_instruction(part2_words)
                            processed_lines.append(f'Caption: "{parts[1].strip()}" {part2_instruction}')
                    elif ',' in text and len(text) > 50:
                        parts = text.split(',', 1)
                        part1_words = len(parts[0].strip().split())
                        part2_words = len(parts[1].strip().split())
                        part1_instruction = self._get_caption_size_instruction(part1_words)
                        part2_instruction = self._get_caption_size_instruction(part2_words)
                        processed_lines.append(f'Caption: "{parts[0].strip()}," {part1_instruction}')
                        processed_lines.append(f'Caption: "{parts[1].strip()}" {part2_instruction}')
                    else:
                        processed_lines.append(f'Caption: "{text}" (RENDER COMPLETE TEXT - USE LARGE CAPTION BOX)')
                else:
                    processed_lines.append(f'Caption: "{text}" {caption_instruction}')
            
            # Handle character dialogue (Name: dialogue or Name (emotion): dialogue)
            elif ':' in line and not line.startswith('Setting:') and not line.startswith('SFX:'):
                # Check if it looks like character dialogue
                parts = line.split(':', 1)
                if len(parts) == 2:
                    speaker = parts[0].strip()
                    dialogue = parts[1].strip()
                    
                    # Check if speaker looks like a character name (could include emotion in parens)
                    if speaker and not any(word in speaker.lower() for word in ['setting', 'panel', 'note']):
                        # Analyze text length for bubble sizing
                        word_count = len(dialogue.split())
                        bubble_instruction = self._get_bubble_size_instruction(word_count)
                        
                        # Break down longer dialogue
                        if len(dialogue) > 35:
                            # Split at natural break points for better rendering
                            if '!' in dialogue and dialogue.index('!') < len(dialogue) - 5:
                                parts = dialogue.split('!', 1)
                                part1_words = len((parts[0].strip() + '!').split())
                                part1_instruction = self._get_bubble_size_instruction(part1_words)
                                processed_lines.append(f'{speaker}: "{parts[0].strip()}!" {part1_instruction}')
                                if parts[1].strip():
                                    part2_words = len(parts[1].strip().split())
                                    part2_instruction = self._get_bubble_size_instruction(part2_words)
                                    processed_lines.append(f'{speaker}: "{parts[1].strip()}" {part2_instruction}')
                            elif '.' in dialogue and dialogue.rindex('.') < len(dialogue) - 1:
                                sentences = dialogue.split('.')
                                for i, sentence in enumerate(sentences):
                                    sentence = sentence.strip()
                                    if sentence:
                                        sent_words = len(sentence.split())
                                        sent_instruction = self._get_bubble_size_instruction(sent_words)
                                        if i == len(sentences) - 1:
                                            processed_lines.append(f'{speaker}: "{sentence}" {sent_instruction}')
                                        else:
                                            processed_lines.append(f'{speaker}: "{sentence}." {sent_instruction}')
                            elif ',' in dialogue:
                                parts = dialogue.split(',', 1)
                                part1_words = len(parts[0].strip().split())
                                part2_words = len(parts[1].strip().split())
                                part1_instruction = self._get_bubble_size_instruction(part1_words)
                                part2_instruction = self._get_bubble_size_instruction(part2_words)
                                processed_lines.append(f'{speaker}: "{parts[0].strip()}," {part1_instruction}')
                                processed_lines.append(f'{speaker}: "{parts[1].strip()}" {part2_instruction}')
                            else:
                                # Add emphasis for complete rendering with large bubble
                                processed_lines.append(f'{speaker}: "{dialogue}" (RENDER ALL WORDS - USE EXTRA LARGE SPEECH BUBBLE)')
                        else:
                            # Handle thought bubbles specially
                            if '(Thought' in speaker or '(thought' in speaker:
                                processed_lines.append(f'{speaker}: "{dialogue}" {bubble_instruction}')
                            else:
                                processed_lines.append(f'{speaker}: "{dialogue}" {bubble_instruction}')
            
            # Handle SFX: lines
            elif line.startswith('SFX:'):
                text = line[4:].strip()
                # Keep sound effects short and punchy
                processed_lines.append(f'SFX: "{text}"')
            
            # Leave other lines unchanged (like Setting: descriptions)
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _get_bubble_size_instruction(self, word_count: int) -> str:
        """Get speech bubble sizing instruction based on word count.
        
        Args:
            word_count: Number of words in the text
            
        Returns:
            Bubble sizing instruction
        """
        if word_count <= 4:
            return "(USE COMPACT SPEECH BUBBLE)"
        elif word_count <= 8:
            return "(USE STANDARD SPEECH BUBBLE WITH PADDING)"
        elif word_count <= 12:
            return "(USE LARGE SPEECH BUBBLE - ARRANGE TEXT IN 2-3 LINES)"
        else:
            return "(USE EXTRA LARGE SPEECH BUBBLE - MULTIPLE LINES WITH GENEROUS SPACING)"
    
    def _get_caption_size_instruction(self, word_count: int) -> str:
        """Get caption box sizing instruction based on word count.
        
        Args:
            word_count: Number of words in the text
            
        Returns:
            Caption box sizing instruction
        """
        if word_count <= 3:
            return "(USE COMPACT CAPTION BOX)"
        elif word_count <= 8:
            return "(USE STANDARD CAPTION BOX)"
        elif word_count <= 15:
            return "(USE LARGE CAPTION BOX - 2-3 LINES)"
        else:
            return "(USE EXTRA LARGE CAPTION BOX - MULTIPLE LINES WITH CLEAR SPACING)"
    
    def _get_panel_position(self, panel_num: int, total_panels: int) -> str:
        """Get position description for a panel.
        
        Args:
            panel_num: Panel number (1-based)
            total_panels: Total number of panels
            
        Returns:
            Position description
        """
        if total_panels == 1:
            return "Full page"
        elif total_panels == 2:
            return "Top half" if panel_num == 1 else "Bottom half"
        elif total_panels == 4:
            positions = ["Top-left", "Top-right", "Bottom-left", "Bottom-right"]
            return positions[panel_num - 1]
        elif total_panels == 6:
            positions = ["Top-left", "Top-right", "Middle-left", "Middle-right", "Bottom-left", "Bottom-right"]
            return positions[panel_num - 1]
        elif total_panels == 9:
            row = (panel_num - 1) // 3
            col = (panel_num - 1) % 3
            rows = ["Top", "Middle", "Bottom"]
            cols = ["left", "center", "right"]
            return f"{rows[row]}-{cols[col]}"
        else:
            return f"Panel {panel_num} of {total_panels}"
    
    def _save_debug_prompt(self, page_number: int, prompt: str):
        """Save debug prompt to file.
        
        Args:
            page_number: Page number
            prompt: Prompt text to save
        """
        from pathlib import Path
        
        if not self.debug_dir:
            return
            
        debug_path = Path(self.debug_dir)
        debug_path.mkdir(parents=True, exist_ok=True)
        
        prompt_file = debug_path / f"page_{page_number:03d}_prompt.txt"
        try:
            with open(prompt_file, 'w') as f:
                f.write(f"=== PROMPT FOR PAGE {page_number} ===\n\n")
                f.write(prompt)
                f.write("\n\n=== END OF PROMPT ===\n")
            logger.debug(f"Saved prompt to {prompt_file}")
        except Exception as e:
            logger.warning(f"Could not save debug prompt: {e}")