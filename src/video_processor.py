# video_processor.py

import os
import gc
import numpy as np
import multiprocessing as mp

# Explicit submodule imports for MoviePy 2.1.2
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip, concatenate_videoclips
from moviepy.audio.AudioClip import CompositeAudioClip

# -------------------- Transition Effect Classes --------------------

class TransitionEffect:
    def __init__(self, duration: float = 1.0):
        self.duration = duration

    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip):
        raise NotImplementedError("Transition effect must implement the apply method.")

class CrossFadeTransition(TransitionEffect):
    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip):
        comp = CompositeVideoClip([
            clip1,
            clip2.set_start(clip1.duration - self.duration)
        ])
        return comp.crossfadein(self.duration)

class SlideTransition(TransitionEffect):
    def __init__(self, duration: float = 1.0, direction: str = 'left'):
        super().__init__(duration)
        self.direction = direction

    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip):
        w, h = clip1.size
        # Map each direction to a function that computes movement at t=1.
        direction_map = {
            'left':  lambda t: ('x', w * t / self.duration),
            'right': lambda t: ('x', -w * t / self.duration),
            'up':    lambda t: ('y', h * t / self.duration),
            'down':  lambda t: ('y', -h * t / self.duration)
        }
        axis, move = direction_map[self.direction](1)
        moving_clip = clip2.set_position(lambda t: {axis: move * (1 - t / self.duration)})
        return CompositeVideoClip([
            clip1,
            moving_clip.set_start(clip1.duration - self.duration)
        ])

class ZoomTransition(TransitionEffect):
    def __init__(self, duration: float = 1.0, zoom_in: bool = True):
        super().__init__(duration)
        self.zoom_in = zoom_in

    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip):
        scale = (lambda t: 0.1 + 0.9 * t / self.duration) if self.zoom_in else \
                (lambda t: 1.9 - 0.9 * t / self.duration)
        zoomed_clip = clip2.resize(lambda t: scale(t))
        return CompositeVideoClip([
            clip1,
            zoomed_clip.set_start(clip1.duration - self.duration)
        ])

# -------------------- VideoProcessor Class --------------------

class VideoProcessor:
    def __init__(self, low_resource_mode=False):
        self.low_resource_mode = low_resource_mode
        # Ensure a default music_track attribute exists.
        self.music_track = None

        self.transitions = {
            'crossfade': CrossFadeTransition,
            'slide_left': lambda d: SlideTransition(d, 'left'),
            'slide_right': lambda d: SlideTransition(d, 'right'),
            'slide_up': lambda d: SlideTransition(d, 'up'),
            'slide_down': lambda d: SlideTransition(d, 'down'),
            'zoom_in': lambda d: ZoomTransition(d, True),
            'zoom_out': lambda d: ZoomTransition(d, False)
        }

        if self.low_resource_mode:
            self.export_presets = {
                'tiktok': {'size': (540, 960), 'fps': 30, 'bitrate': '4000k', 'audio_bitrate': '128k'},
                'instagram': {'size': (540, 540), 'fps': 24, 'bitrate': '3500k', 'audio_bitrate': '128k'},
                'youtube': {'size': (1280, 720), 'fps': 30, 'bitrate': '6000k', 'audio_bitrate': '192k'}
            }
        else:
            self.export_presets = {
                'tiktok': {'size': (1080, 1920), 'fps': 60, 'bitrate': '8000k', 'audio_bitrate': '192k'},
                'instagram': {'size': (1080, 1080), 'fps': 30, 'bitrate': '6000k', 'audio_bitrate': '192k'},
                'youtube': {'size': (1920, 1080), 'fps': 60, 'bitrate': '12000k', 'audio_bitrate': '320k'}
            }

    def process_video(self, clips, style_params, viral_params):
        # Create a hook clip from the first clip.
        hook_clip = clips[0].subclip(0, min(viral_params.get('hook_duration', 3), clips[0].duration))
        hook_clip = hook_clip.resize(lambda t: 1 + 0.1 * t)
        processed_clips = [hook_clip]

        for i, clip in enumerate(clips[1:], 1):
            duration = style_params.get('pacing', 1.0) * clip.duration
            processed_clip = clip.subclip(0, duration)
            if i > 0:
                transition = self._get_transition(processed_clips[-1], processed_clip, style_params)
                processed_clips[-1] = transition
            processed_clips.append(processed_clip)

        final_video = concatenate_videoclips(processed_clips, method="compose")
        if self.music_track:
            final_video = self._add_music(final_video)

        return final_video

    def _get_transition(self, clip1, clip2, style_params):
        if self.low_resource_mode:
            fade = CrossFadeTransition(duration=0.5)
            return fade.apply(clip1, clip2)
        else:
            t_type = np.random.choice(list(self.transitions.keys()))
            transition = self.transitions[t_type](style_params.get('transition_frequency', 1.0))
            return transition.apply(clip1, clip2)

    def _add_music(self, video):
        music = self.music_track
        if music.duration > video.duration:
            music = music.subclip(0, video.duration)
        else:
            music = music.loop(duration=video.duration)
        music = music.volumex(0.6)
        return video.set_audio(CompositeAudioClip([video.audio, music]))

    def export_video(self, video, output_path, format='mp4', preset='youtube'):
        settings = self.export_presets[preset]
        video = video.resize(settings['size'])
        # Refresh the frame pipeline
        video = video.fl_image(lambda frame: frame)

        format_settings = {
            'mp4': {'codec': 'libx264', 'audio_codec': 'aac'},
            'mkv': {'codec': 'libx264', 'audio_codec': 'aac'},
            'avi': {'codec': 'libx264', 'audio_codec': 'mp3'},
            'mov': {'codec': 'libx264', 'audio_codec': 'aac'}
        }
        ffmpeg_preset = 'ultrafast' if self.low_resource_mode else 'faster'
        video.write_videofile(
            output_path,
            fps=settings['fps'],
            codec=format_settings[format]['codec'],
            audio_codec=format_settings[format]['audio_codec'],
            bitrate=settings['bitrate'],
            audio_bitrate=settings['audio_bitrate'],
            threads=1,
            preset=ffmpeg_preset,
            remove_temp=True
        )

        if hasattr(video.reader, 'close_proc'):
            video.reader.close_proc()

        gc.collect()

# -------------------- Subprocess Export Function --------------------

def export_video_in_subprocess(video, output_path, format, preset, low_resource_mode):
    """
    This function runs in a separate process to export the video.
    """
    processor = VideoProcessor(low_resource_mode=low_resource_mode)
    processor.export_video(video, output_path, format, preset)

# -------------------- Export Wrapper --------------------

def export_video_wrapper(video, output_path, format='mp4', preset='youtube', low_resource_mode=False):
    """
    Spawns a separate process to export the video.
    """
    p = mp.Process(target=export_video_in_subprocess, args=(video, output_path, format, preset, low_resource_mode))
    p.start()
    p.join()
