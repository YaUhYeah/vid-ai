import cv2
import numpy as np
from typing import List, Tuple
from moviepy import VideoFileClip

class SceneDetector:
    def __init__(self, threshold: float = 30.0, min_scene_length: float = 0.5):
        self.threshold = threshold
        self.min_scene_length = min_scene_length
    
    def detect_scenes(self, video_path: str) -> List[Tuple[float, float]]:
        """Detect scene changes in a video file."""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        scenes = []
        prev_frame = None
        scene_start = 0
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Convert frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame is not None:
                # Calculate difference between frames
                diff = cv2.absdiff(gray, prev_frame)
                mean_diff = np.mean(diff)
                
                # If difference exceeds threshold, mark as scene change
                if mean_diff > self.threshold:
                    frame_time = frame_count / fps
                    if frame_time - scene_start >= self.min_scene_length:
                        scenes.append((scene_start, frame_time))
                        scene_start = frame_time
            
            prev_frame = gray
            frame_count += 1
        
        # Add final scene
        if frame_count > 0:
            scenes.append((scene_start, frame_count / fps))
        
        cap.release()
        return scenes
    
    def get_scene_thumbnails(self, video_path: str, scenes: List[Tuple[float, float]]) -> List[np.ndarray]:
        """Extract thumbnail frames for each detected scene."""
        thumbnails = []
        cap = cv2.VideoCapture(video_path)
        
        for start, _ in scenes:
            cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
            ret, frame = cap.read()
            if ret:
                thumbnails.append(frame)
        
        cap.release()
        return thumbnails
    
    def auto_cut(self, clip: VideoFileClip, scenes: List[Tuple[float, float]]) -> List[VideoFileClip]:
        """Cut video into subclips based on detected scenes."""
        return [clip.with_section_cut_out(start, end) for start, end in scenes]