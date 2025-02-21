from abc import ABC, abstractmethod
from moviepy.editor import VideoFileClip, CompositeVideoClip
from typing import Tuple, Optional, Dict, Any

class TransitionEffect(ABC):
    """Base class for all transition effects"""
    
    def __init__(self, duration: float = 1.0, **kwargs):
        self.duration = duration
        self.params = kwargs
    
    @abstractmethod
    def apply(self, clip1: VideoFileClip, clip2: VideoFileClip) -> VideoFileClip:
        """Apply the transition effect between two clips"""
        pass
    
    def get_params(self) -> Dict[str, Any]:
        """Get the current parameters of the transition"""
        return {
            'duration': self.duration,
            **self.params
        }
    
    def set_params(self, **kwargs):
        """Update the transition parameters"""
        if 'duration' in kwargs:
            self.duration = kwargs.pop('duration')
        self.params.update(kwargs)
    
    @property
    def name(self) -> str:
        """Get the name of the transition effect"""
        return self.__class__.__name__