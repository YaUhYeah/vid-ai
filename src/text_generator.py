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
        words = prompt.split()
        if len(words) < 10:
            # For very short prompts, just return the prompt as title.
            return prompt.strip().title()
        # Set parameters relative to the input length.
        max_length = min(10, len(words))
        min_length = min(5, len(words))
        summary = self.summarizer(
            prompt,
            max_length=max_length,
            min_length=min_length,
            truncation=True
        )[0]['summary_text']
        return summary.strip().title()

    def generate_captions(self, prompt: str, num_captions: int = 3) -> List[str]:
        words = prompt.split()
        # If the prompt is too short, return a list with the prompt repeated.
        if len(words) < 15:
            return [prompt.strip()] * num_captions
        # Adjust the overall length based on input.
        total_max = min(30 * num_captions, len(words) * 2)
        total_min = min(10, len(words))
        summary = self.summarizer(
            prompt,
            max_length=total_max,
            min_length=total_min,
            truncation=True
        )[0]['summary_text']
        sentences = summary.split('.')
        return [s.strip() for s in sentences if s.strip()][:num_captions]

    def create_text_overlay(self,
                            frame: np.ndarray,
                            text: str,
                            position: str = 'center',
                            style: str = 'title',
                            color: tuple = (255, 255, 255),
                            shadow: bool = True) -> np.ndarray:
        # Ensure the input is a numpy array
        if not isinstance(frame, np.ndarray):
            try:
                frame = np.array(frame)
            except Exception as e:
                print("Error converting frame to numpy array:", e)
                return frame  # Return unmodified if conversion fails

        # Wrap the cvtColor call in a try/except to catch unexpected issues
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        except Exception as e:
            print("Error in cv2.cvtColor:", e)
            frame_rgb = frame  # Fallback: use original frame

        frame_pil = Image.fromarray(frame_rgb)
        draw = ImageDraw.Draw(frame_pil)

        # Load font (fallback to default if not found)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                                      self.font_sizes[style])
        except Exception:
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

        # Draw shadow if requested
        if shadow:
            shadow_offset = max(2, self.font_sizes[style] // 20)
            draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0))

        # Draw main text
        draw.text((x, y), text, font=font, fill=color)

        # Convert back to numpy array and return
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