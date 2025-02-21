from transformers import pipeline
from typing import List, Dict, Any
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2

class TextGenerator:
    def __init__(self):
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        self.font_sizes = {
            'title': 72,
            'subtitle': 48,
            'body': 36,
            'caption': 24
        }
        
    def generate_title(self, prompt: str) -> str:
        """Generate an engaging title from the prompt."""
        summary = self.summarizer(prompt, max_length=10, min_length=5)[0]['summary_text']
        return summary.strip().title()
    
    def generate_captions(self, prompt: str, num_captions: int = 3) -> List[str]:
        """Generate multiple captions from the prompt."""
        summary = self.summarizer(prompt, max_length=30 * num_captions, min_length=10)[0]['summary_text']
        sentences = summary.split('.')
        return [s.strip() for s in sentences if s.strip()][:num_captions]
    
    def create_text_overlay(self, 
                          frame: np.ndarray,
                          text: str,
                          position: str = 'center',
                          style: str = 'title',
                          color: tuple = (255, 255, 255),
                          shadow: bool = True) -> np.ndarray:
        """Create a text overlay on a video frame."""
        # Convert frame to PIL Image
        frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(frame_pil)
        
        # Load font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                                    self.font_sizes[style])
        except:
            font = ImageFont.load_default()
        
        # Calculate text size and position
        text_width, text_height = draw.textsize(text, font=font)
        frame_width, frame_height = frame.shape[1], frame.shape[0]
        
        positions = {
            'center': ((frame_width - text_width) // 2, (frame_height - text_height) // 2),
            'top': ((frame_width - text_width) // 2, text_height),
            'bottom': ((frame_width - text_width) // 2, frame_height - text_height * 2),
            'top-left': (text_height, text_height),
            'top-right': (frame_width - text_width - text_height, text_height),
            'bottom-left': (text_height, frame_height - text_height * 2),
            'bottom-right': (frame_width - text_width - text_height, frame_height - text_height * 2)
        }
        
        x, y = positions.get(position, positions['center'])
        
        # Add shadow if requested
        if shadow:
            shadow_offset = max(2, self.font_sizes[style] // 20)
            draw.text((x + shadow_offset, y + shadow_offset), text, 
                     font=font, fill=(0, 0, 0))
        
        # Draw text
        draw.text((x, y), text, font=font, fill=color)
        
        # Convert back to numpy array
        return cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)
    
    def create_animated_text(self,
                           frame: np.ndarray,
                           text: str,
                           t: float,
                           duration: float,
                           animation: str = 'fade',
                           **kwargs) -> np.ndarray:
        """Create animated text overlay."""
        if animation == 'fade':
            alpha = min(1.0, 2 * t/duration) if t < duration/2 else min(1.0, 2 * (1 - t/duration))
            color = list(kwargs.get('color', (255, 255, 255)))
            if len(color) == 3:
                color.append(int(255 * alpha))
            kwargs['color'] = tuple(color)
            
        elif animation == 'slide':
            offset = int((1 - t/duration) * frame.shape[1])
            if 'position' in kwargs:
                pos = kwargs['position'].split('-')
                if 'right' in pos:
                    offset = -offset
                kwargs['position'] = f"{pos[0]}-{pos[1]}-{offset}"
        
        return self.create_text_overlay(frame, text, **kwargs)
    
    def generate_thumbnail_text(self, prompt: str) -> Dict[str, str]:
        """Generate text elements for thumbnail."""
        title = self.generate_title(prompt)
        subtitle = self.generate_captions(prompt, num_captions=1)[0]
        
        return {
            'title': title,
            'subtitle': subtitle
        }