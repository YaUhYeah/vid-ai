from moviepy.editor import VideoFileClip, CompositeVideoClip, clips_array, vfx
import numpy as np
from .base import TransitionEffect

class CrossFadeTransition(TransitionEffect):
    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip) -> VideoFileClip:
        return CompositeVideoClip([
            clip1,
            clip2.set_start(clip1.duration - self.duration)
        ]).crossfadein(self.duration)

class SlideTransition(TransitionEffect):
    def __init__(self, duration: float = 1.0, direction: str = 'left'):
        super().__init__(duration, direction=direction)
    
    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip) -> VideoFileClip:
        w, h = clip1.size
        direction = self.params['direction']
        
        direction_map = {
            'left': lambda t: ('x', w * t / self.duration),
            'right': lambda t: ('x', -w * t / self.duration),
            'up': lambda t: ('y', h * t / self.duration),
            'down': lambda t: ('y', -h * t / self.duration)
        }
        
        axis, move = direction_map[direction](1)
        moving_clip = clip2.set_position(lambda t: {axis: move * (1 - t/self.duration)})
        
        return CompositeVideoClip([
            clip1,
            moving_clip.set_start(clip1.duration - self.duration)
        ])

class ZoomTransition(TransitionEffect):
    def __init__(self, duration: float = 1.0, zoom_in: bool = True):
        super().__init__(duration, zoom_in=zoom_in)
    
    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip) -> VideoFileClip:
        zoom_in = self.params['zoom_in']
        scale = lambda t: 0.1 + 0.9 * t/self.duration if zoom_in else 1.9 - 0.9 * t/self.duration
        zoomed_clip = clip2.resize(lambda t: scale(t))
        
        return CompositeVideoClip([
            clip1,
            zoomed_clip.set_start(clip1.duration - self.duration)
        ])

class WhipTransition(TransitionEffect):
    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip) -> VideoFileClip:
        w, h = clip1.size
        whip = (lambda t: min(w * 2, w * 4 * t/self.duration))
        
        clip1 = clip1.set_position(lambda t: ('x', whip(t)))
        clip2 = clip2.set_position(lambda t: ('x', -w + whip(t)))
        
        return CompositeVideoClip([
            clip1,
            clip2.set_start(clip1.duration - self.duration)
        ])

class RotateTransition(TransitionEffect):
    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip) -> VideoFileClip:
        rotate1 = clip1.rotate(lambda t: 90 * t/self.duration)
        rotate2 = clip2.rotate(lambda t: -90 * (1 - t/self.duration))
        
        return CompositeVideoClip([
            rotate1,
            rotate2.set_start(clip1.duration - self.duration)
        ])

class FlashTransition(TransitionEffect):
    def __init__(self, duration: float = 0.5, flash_color: str = 'white'):
        super().__init__(duration, flash_color=flash_color)
    
    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip) -> VideoFileClip:
        flash_color = self.params['flash_color']
        w, h = clip1.size
        
        # Create flash clip
        flash = ColorClip(size=(w, h), color=flash_color, duration=self.duration/2)
        flash = flash.set_opacity(lambda t: np.sin(np.pi * t/(self.duration/2)))
        
        return CompositeVideoClip([
            clip1,
            flash.set_start(clip1.duration - self.duration),
            clip2.set_start(clip1.duration - self.duration/2)
        ])

class GlitchTransition(TransitionEffect):
    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip) -> VideoFileClip:
        def glitch_effect(get_frame, t):
            frame = get_frame(t)
            
            # Random glitch parameters
            n_glitches = np.random.randint(5, 15)
            glitch_positions = np.random.randint(0, frame.shape[0], n_glitches)
            glitch_widths = np.random.randint(5, 20, n_glitches)
            
            # Apply glitches
            for pos, width in zip(glitch_positions, glitch_widths):
                if pos + width < frame.shape[0]:
                    frame[pos:pos+width] = np.roll(frame[pos:pos+width], 
                                                 np.random.randint(-50, 50), axis=1)
            
            return frame
        
        glitch1 = clip1.fl(glitch_effect)
        glitch2 = clip2.fl(glitch_effect)
        
        return CompositeVideoClip([
            glitch1,
            glitch2.set_start(clip1.duration - self.duration)
        ]).crossfadein(self.duration)

class PixelateTransition(TransitionEffect):
    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip) -> VideoFileClip:
        def pixelate(get_frame, t):
            frame = get_frame(t)
            ratio = t / self.duration
            pixel_size = int(max(1, 50 * (1 - ratio)))
            
            if pixel_size > 1:
                h, w = frame.shape[:2]
                temp = cv2.resize(frame, (w // pixel_size, h // pixel_size),
                                interpolation=cv2.INTER_LINEAR)
                return cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
            return frame
        
        pixelated1 = clip1.fl(pixelate)
        pixelated2 = clip2.fl(pixelate)
        
        return CompositeVideoClip([
            pixelated1,
            pixelated2.set_start(clip1.duration - self.duration)
        ]).crossfadein(self.duration)

# Registry of all available transitions
TRANSITIONS = {
    'crossfade': CrossFadeTransition,
    'slide_left': lambda d: SlideTransition(d, 'left'),
    'slide_right': lambda d: SlideTransition(d, 'right'),
    'slide_up': lambda d: SlideTransition(d, 'up'),
    'slide_down': lambda d: SlideTransition(d, 'down'),
    'zoom_in': lambda d: ZoomTransition(d, True),
    'zoom_out': lambda d: ZoomTransition(d, False),
    'whip': WhipTransition,
    'rotate': RotateTransition,
    'flash': FlashTransition,
    'glitch': GlitchTransition,
    'pixelate': PixelateTransition
}