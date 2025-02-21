from PyQt5.QtWidgets import (QWidget, QScrollArea, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QPainter, QColor, QPen, QLinearGradient, QImage, QPixmap
import numpy as np
from moviepy.editor import VideoFileClip
import librosa

class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.waveform_data = None
        self.setMinimumHeight(50)
        self.setMaximumHeight(100)
        
    def set_audio_data(self, audio_path: str):
        """Load and process audio data for visualization."""
        y, sr = librosa.load(audio_path)
        # Get waveform envelope
        self.waveform_data = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        self.update()
        
    def paintEvent(self, event):
        if self.waveform_data is None:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(52, 152, 219))
        gradient.setColorAt(1, QColor(41, 128, 185))
        
        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(gradient)
        
        # Draw waveform
        width = self.width()
        height = self.height()
        points_per_pixel = max(1, len(self.waveform_data) // width)
        
        for x in range(width):
            start_idx = x * points_per_pixel
            end_idx = start_idx + points_per_pixel
            if start_idx >= len(self.waveform_data):
                break
                
            chunk = self.waveform_data[start_idx:end_idx]
            if len(chunk) > 0:
                value = np.mean(chunk)
                scaled_value = value * height
                
                painter.drawRect(
                    x,
                    height//2 - scaled_value//2,
                    1,
                    scaled_value
                )

class TimelineClip(QWidget):
    clicked = pyqtSignal(int)  # Clip index
    moved = pyqtSignal(int, int)  # Old index, new index
    
    def __init__(self, index: int, thumbnail: QImage, duration: float, parent=None):
        super().__init__(parent)
        self.index = index
        self.thumbnail = thumbnail
        self.duration = duration
        self.setFixedHeight(80)
        self.setMinimumWidth(int(duration * 50))  # 50 pixels per second
        
        self.setStyleSheet("""
            QWidget {
                background-color: #2C2C2C;
                border: 1px solid #3C3C3C;
                border-radius: 4px;
            }
            QWidget:hover {
                background-color: #3C3C3C;
            }
        """)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw thumbnail
        if self.thumbnail:
            scaled_thumb = self.thumbnail.scaledToHeight(
                self.height(), Qt.SmoothTransformation)
            painter.drawImage(0, 0, scaled_thumb)
        
        # Draw duration text
        painter.setPen(Qt.white)
        duration_text = f"{self.duration:.1f}s"
        painter.drawText(
            self.width() - 50, self.height() - 20,
            40, 20,
            Qt.AlignRight | Qt.AlignBottom,
            duration_text
        )
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)
            
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(str(self.index))
            drag.setMimeData(mime_data)
            drag.exec_(Qt.MoveAction)

class TimelineWidget(QWidget):
    clip_selected = pyqtSignal(int)  # Clip index
    clips_reordered = pyqtSignal(list)  # New clip order
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Timeline controls
        controls_layout = QHBoxLayout()
        self.zoom_in_btn = QPushButton("+")
        self.zoom_out_btn = QPushButton("-")
        self.play_btn = QPushButton("▶")
        
        for btn in [self.zoom_in_btn, self.zoom_out_btn, self.play_btn]:
            btn.setFixedSize(30, 30)
            controls_layout.addWidget(btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Timeline scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Timeline content
        self.timeline_content = QWidget()
        self.timeline_layout = QHBoxLayout(self.timeline_content)
        self.timeline_layout.setSpacing(2)
        self.timeline_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.timeline_content)
        layout.addWidget(self.scroll_area)
        
        # Waveform
        self.waveform = WaveformWidget()
        layout.addWidget(self.waveform)
        
        # Connect signals
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.play_btn.clicked.connect(self.toggle_play)
        
    def add_clip(self, clip: VideoFileClip, thumbnail: QImage = None):
        """Add a new clip to the timeline."""
        index = self.timeline_layout.count()
        clip_widget = TimelineClip(index, thumbnail, clip.duration)
        
        clip_widget.clicked.connect(self.clip_selected.emit)
        clip_widget.moved.connect(self.handle_clip_moved)
        
        self.timeline_layout.addWidget(clip_widget)
        
    def set_audio_waveform(self, audio_path: str):
        """Set audio waveform data."""
        self.waveform.set_audio_data(audio_path)
        
    def zoom_in(self):
        """Increase timeline zoom level."""
        for i in range(self.timeline_layout.count()):
            clip = self.timeline_layout.itemAt(i).widget()
            clip.setMinimumWidth(int(clip.minimumWidth() * 1.2))
            
    def zoom_out(self):
        """Decrease timeline zoom level."""
        for i in range(self.timeline_layout.count()):
            clip = self.timeline_layout.itemAt(i).widget()
            clip.setMinimumWidth(max(50, int(clip.minimumWidth() / 1.2)))
            
    def toggle_play(self):
        """Toggle timeline playback."""
        if self.play_btn.text() == "▶":
            self.play_btn.setText("⏸")
        else:
            self.play_btn.setText("▶")
            
    def handle_clip_moved(self, old_index: int, new_index: int):
        """Handle clip reordering."""
        if 0 <= new_index < self.timeline_layout.count():
            # Get the widget
            widget = self.timeline_layout.takeAt(old_index).widget()
            
            # Update indices
            widget.index = new_index
            self.timeline_layout.insertWidget(new_index, widget)
            
            # Emit new order
            new_order = []
            for i in range(self.timeline_layout.count()):
                clip = self.timeline_layout.itemAt(i).widget()
                new_order.append(clip.index)
            
            self.clips_reordered.emit(new_order)
            
    def clear(self):
        """Clear all clips from timeline."""
        while self.timeline_layout.count():
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()