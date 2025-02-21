# AI-Edit Pro

An AI-powered video editor that helps you create viral content with ease. Simply describe your vision, import your media, and let AI handle the editing.

## Features

- AI-driven video editing based on natural language prompts
- Multiple transition effects with customizable parameters
- Support for various video formats (MP4, MKV, AVI, MOV)
- Optimized export presets for different platforms (YouTube, Instagram, TikTok)
- Modern, user-friendly interface
- Drag-and-drop media import
- Real-time preview
- Background processing

## Installation

```bash
pip install ai-edit-pro
```

## Usage

1. Launch the application:
```bash
ai-edit-pro
```

2. Enter your video requirements in the prompt box
3. Import your media files (videos, audio, images)
4. Choose your export format and platform
5. Click "Generate Viral Video" and wait for processing

## For Developers

### Adding Custom Transitions

You can create custom transition effects by inheriting from the `TransitionEffect` base class:

```python
from ai_edit_pro.transitions import TransitionEffect
from moviepy.editor import VideoFileClip, CompositeVideoClip

class MyCustomTransition(TransitionEffect):
    def __init__(self, duration: float = 1.0, **kwargs):
        super().__init__(duration, **kwargs)
    
    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip) -> VideoFileClip:
        # Implement your transition logic here
        return CompositeVideoClip([clip1, clip2])

# Register your transition
from ai_edit_pro.transitions.effects import TRANSITIONS
TRANSITIONS['my_custom'] = MyCustomTransition
```

### Export Presets

You can modify export presets in the `video_processor.py` file:

```python
export_presets = {
    'custom_preset': {
        'size': (1920, 1080),
        'fps': 60,
        'bitrate': '12000k',
        'audio_bitrate': '320k'
    }
}
```

## Requirements

- Python 3.8 or higher
- FFmpeg
- GPU recommended for faster processing

## License

MIT License