from moviepy.editor import *
from moviepy.video.tools.segmenting import findObjects
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
import json

class TransitionEffect:
    """Base class for transition effects"""
    def __init__(self, duration: float = 1.0):
        self.duration = duration
    
    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip) -> VideoFileClip:
        raise NotImplementedError

class CrossFadeTransition(TransitionEffect):
    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip) -> VideoFileClip:
        return CompositeVideoClip([
            clip1,
            clip2.set_start(clip1.duration - self.duration)
        ]).crossfadein(self.duration)

class SlideTransition(TransitionEffect):
    def __init__(self, duration: float = 1.0, direction: str = 'left'):
        super().__init__(duration)
        self.direction = direction
    
    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip) -> VideoFileClip:
        w, h = clip1.size
        direction_map = {
            'left': lambda t: ('x', w * t / self.duration),
            'right': lambda t: ('x', -w * t / self.duration),
            'up': lambda t: ('y', h * t / self.duration),
            'down': lambda t: ('y', -h * t / self.duration)
        }
        
        axis, move = direction_map[self.direction](1)
        moving_clip = clip2.set_position(lambda t: {axis: move * (1 - t/self.duration)})
        
        return CompositeVideoClip([
            clip1,
            moving_clip.set_start(clip1.duration - self.duration)
        ])

class ZoomTransition(TransitionEffect):
    def __init__(self, duration: float = 1.0, zoom_in: bool = True):
        super().__init__(duration)
        self.zoom_in = zoom_in
    
    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip) -> VideoFileClip:
        scale = lambda t: 0.1 + 0.9 * t/self.duration if self.zoom_in else 1.9 - 0.9 * t/self.duration
        zoomed_clip = clip2.resize(lambda t: scale(t))
        return CompositeVideoClip([
            clip1,
            zoomed_clip.set_start(clip1.duration - self.duration)
        ])

class VideoProcessor:
    def __init__(self):
        self.transitions = {
            'crossfade': CrossFadeTransition,
            'slide_left': lambda d: SlideTransition(d, 'left'),
            'slide_right': lambda d: SlideTransition(d, 'right'),
            'slide_up': lambda d: SlideTransition(d, 'up'),
            'slide_down': lambda d: SlideTransition(d, 'down'),
            'zoom_in': lambda d: ZoomTransition(d, True),
            'zoom_out': lambda d: ZoomTransition(d, False)
        }
        
        # Video export presets optimized for different platforms
        self.export_presets = {
            'tiktok': {
                'size': (1080, 1920),
                'fps': 60,
                'bitrate': '8000k',
                'audio_bitrate': '192k'
            },
            'instagram': {
                'size': (1080, 1080),
                'fps': 30,
                'bitrate': '6000k',
                'audio_bitrate': '192k'
            },
            'youtube': {
                'size': (1920, 1080),
                'fps': 60,
                'bitrate': '12000k',
                'audio_bitrate': '320k'
            }
        }
    
    def add_custom_transition(self, name: str, transition_class: type):
        """API for adding custom transition effects"""
        if not issubclass(transition_class, TransitionEffect):
            raise ValueError("Custom transition must inherit from TransitionEffect")
        self.transitions[name] = transition_class
    
    def process_video(self, 
                     clips: List[VideoFileClip],
                     style_params: Dict[str, float],
                     viral_params: Dict[str, float]) -> VideoFileClip:
        """Process video clips according to style and viral parameters"""
        
        # Apply viral optimization
        hook_clip = self._create_hook(clips[0], viral_params['hook_duration'])
        processed_clips = [hook_clip]
        
        # Process remaining clips
        for i, clip in enumerate(clips[1:], 1):
            # Adjust clip duration based on engagement
            duration = style_params['pacing'] * clip.duration
            processed_clip = clip.subclip(0, duration)
            
            # Apply transition
            if i > 0:
                transition = self._get_transition(processed_clips[-1], processed_clip, style_params)
                processed_clips[-1] = transition
            
            processed_clips.append(processed_clip)
        
        # Concatenate all clips
        final_video = concatenate_videoclips(processed_clips)
        
        # Add music if provided
        if hasattr(self, 'music_track'):
            final_video = self._add_music(final_video)
        
        return final_video
    
    def _create_hook(self, clip: VideoFileClip, duration: float) -> VideoFileClip:
        """Create an attention-grabbing hook from the first clip"""
        hook = clip.subclip(0, min(duration, clip.duration))
        
        # Add zoom effect
        hook = hook.resize(lambda t: 1 + 0.1 * t)
        
        # Add text overlay if needed
        # hook = self._add_hook_text(hook)
        
        return hook
    
    def _get_transition(self, 
                       clip1: VideoFileClip, 
                       clip2: VideoFileClip, 
                       style_params: Dict[str, float]) -> VideoFileClip:
        """Select and apply appropriate transition"""
        transition_type = np.random.choice(list(self.transitions.keys()))
        transition = self.transitions[transition_type](style_params['transition_frequency'])
        return transition.apply(clip1, clip2)
    
    def _add_music(self, video: VideoFileClip) -> VideoFileClip:
        """Add background music with beat-synced transitions"""
        music = self.music_track
        if music.duration > video.duration:
            music = music.subclip(0, video.duration)
        else:
            music = music.loop(duration=video.duration)
        
        # Normalize audio levels
        music = music.volumex(0.6)  # Background music at 60% volume
        
        return video.set_audio(CompositeAudioClip([video.audio, music]))
    
    def export_video(self, 
                    video: VideoFileClip,
                    output_path: str,
                    format: str = 'mp4',
                    preset: str = 'youtube') -> None:
        """Export video with optimized settings for viral content"""
        
        # Get export settings
        settings = self.export_presets[preset].copy()
        
        # Adjust video size and settings
        video = video.resize(settings['size'])
        
        # Export with format-specific settings
        format_settings = {
            'mp4': {'codec': 'libx264', 'audio_codec': 'aac'},
            'mkv': {'codec': 'libx264', 'audio_codec': 'aac'},
            'avi': {'codec': 'libx264', 'audio_codec': 'mp3'},
            'mov': {'codec': 'libx264', 'audio_codec': 'aac'}
        }
        
        video.write_videofile(
            output_path,
            fps=settings['fps'],
            codec=format_settings[format]['codec'],
            audio_codec=format_settings[format]['audio_codec'],
            bitrate=settings['bitrate'],
            audio_bitrate=settings['audio_bitrate'],
            threads=4,
            preset='faster'  # Use 'faster' preset for quicker encoding
        )