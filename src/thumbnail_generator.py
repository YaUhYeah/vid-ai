import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from typing import Dict
from text_generator import TextGenerator


class ThumbnailGenerator:
    def __init__(self):
        self.text_generator = TextGenerator()
        self.sizes = {
            'youtube': (1280, 720),
            'instagram': (1080, 1080),
            'tiktok': (1080, 1920)
        }

    def generate_thumbnail(self,
                           frame: np.ndarray,
                           text: Dict[str, str],
                           platform: str = 'youtube',
                           style: str = 'modern') -> np.ndarray:
        # Ensure the frame is a valid numpy array
        if not isinstance(frame, np.ndarray):
            try:
                frame = np.array(frame)
            except Exception as e:
                print("Error converting frame to numpy array in generate_thumbnail:", e)
                return frame

        try:
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        except Exception as e:
            print("Error converting frame color in generate_thumbnail:", e)
            image = Image.fromarray(frame)  # fallback without color conversion

        # Resize to platform-specific dimensions
        size = self.sizes.get(platform, self.sizes['youtube'])
        image = image.resize(size, Image.LANCZOS)

        # Apply style-specific enhancements and add text overlays
        image = self._apply_style(image, style)
        image = self._add_text_overlays(image, text)
        # Ensure the image is in RGB mode
        image = image.convert("RGB")
        # Use np.asarray and cast to uint8 explicitly
        im_array = np.asarray(image).astype('uint8')
        return cv2.cvtColor(im_array, cv2.COLOR_RGB2BGR)

    def _apply_style(self, image: Image, style: str) -> Image:
        """Apply visual style to the thumbnail."""
        if style == 'modern':
            # Increase contrast and saturation
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.3)
            # Add subtle blur to background
            bg = image.filter(ImageFilter.GaussianBlur(radius=3))
            image = Image.blend(image, bg, 0.3)
        elif style == 'minimal':
            # Reduce saturation and add brightness
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(0.8)
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.1)
        elif style == 'vibrant':
            # High contrast and saturation
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.4)
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.5)
            # Add vignette effect
            image = self._add_vignette(image)
        return image

    def _add_text_overlays(self, image: Image, text: Dict[str, str]) -> Image:
        """Add text overlays to the thumbnail."""
        draw = ImageDraw.Draw(image)
        width, height = image.size
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

        # Add title
        if 'title' in text:
            title_text = text['title']
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            x = (width - title_width) // 2
            y = height - title_height - 100
            shadow_offset = 3
            draw.text((x + shadow_offset, y + shadow_offset), title_text, font=title_font, fill=(0, 0, 0, 180))
            draw.text((x, y), title_text, font=title_font, fill=(255, 255, 255))

        # Add subtitle
        if 'subtitle' in text:
            subtitle_text = text['subtitle']
            subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            x = (width - subtitle_width) // 2
            y = height - 60
            shadow_offset = 2
            draw.text((x + shadow_offset, y + shadow_offset), subtitle_text, font=subtitle_font, fill=(0, 0, 0, 180))
            draw.text((x, y), subtitle_text, font=subtitle_font, fill=(255, 255, 255))

        return image

    def _add_vignette(self, image: Image, intensity: float = 0.3) -> Image:
        """Add vignette effect to the image."""
        width, height = image.size
        mask = Image.new('L', (width, height))
        mask_draw = ImageDraw.Draw(mask)
        for i in range(min(width, height) // 2):
            alpha = int(255 * (1 - i / (min(width, height) // 2) * intensity))
            mask_draw.ellipse([i, i, width - i, height - i], fill=alpha)
        return Image.composite(image, Image.new('RGB', (width, height), 'black'), mask)

    def extract_best_frame(self, video_path: str, num_samples: int = 10) -> np.ndarray:
        """Extract the best frame for thumbnail from video."""
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        best_frame = None
        best_score = -1
        for i in range(num_samples):
            frame_pos = int((i + 1) * total_frames / (num_samples + 1))
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = cap.read()
            if not ret:
                continue
            score = self._calculate_frame_score(frame)
            if score > best_score:
                best_score = score
                best_frame = frame
        cap.release()
        return best_frame if best_frame is not None else None

    def _calculate_frame_score(self, frame: np.ndarray) -> float:
        """Calculate a score for frame quality."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        contrast = np.std(gray)
        brightness = np.mean(gray)
        blur = cv2.Laplacian(gray, cv2.CV_64F).var()
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        face_score = len(faces) * 50
        score = (contrast * 0.5 +
                 min(brightness, 255 - brightness) * 0.3 +
                 min(blur, 1000) * 0.2 +
                 face_score)
        return score
