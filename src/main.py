import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QTextEdit, QLabel,
                           QFileDialog, QProgressBar, QFrame, QComboBox,
                           QListWidget, QMessageBox, QSplitter, QTabWidget)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QDragEnterEvent, QDropEvent, QImage
from moviepy.editor import VideoFileClip, AudioFileClip
from .ai_processor import AIProcessor
from .video_processor import VideoProcessor
from .scene_detector import SceneDetector
from .text_generator import TextGenerator
from .thumbnail_generator import ThumbnailGenerator
from .timeline_widget import TimelineWidget

class ProcessingThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    scene_detected = pyqtSignal(list)  # List of scene timestamps
    thumbnail_generated = pyqtSignal(object)  # Thumbnail image
    text_generated = pyqtSignal(dict)  # Generated text overlays

    def __init__(self, clips, prompt, output_path, format_preset):
        super().__init__()
        self.clips = clips
        self.prompt = prompt
        self.output_path = output_path
        self.format_preset = format_preset
        
        # Initialize processors
        self.ai_processor = AIProcessor()
        self.video_processor = VideoProcessor()
        self.scene_detector = SceneDetector()
        self.text_generator = TextGenerator()
        self.thumbnail_generator = ThumbnailGenerator()
        
    def run(self):
        try:
            # Step 1: Analyze prompt and get style parameters
            self.progress.emit(10)
            style_params = self.ai_processor.analyze_prompt(self.prompt)
            
            # Step 2: Detect scenes in each clip
            self.progress.emit(20)
            all_scenes = []
            for clip in self.clips:
                scenes = self.scene_detector.detect_scenes(clip.filename)
                all_scenes.extend(scenes)
            self.scene_detected.emit(all_scenes)
            
            # Step 3: Generate text overlays
            self.progress.emit(30)
            text_overlays = {
                'title': self.text_generator.generate_title(self.prompt),
                'captions': self.text_generator.generate_captions(self.prompt)
            }
            self.text_generated.emit(text_overlays)
            
            # Step 4: Generate thumbnail
            self.progress.emit(40)
            best_frame = self.thumbnail_generator.extract_best_frame(self.clips[0].filename)
            if best_frame is not None:
                thumbnail = self.thumbnail_generator.generate_thumbnail(
                    best_frame,
                    {'title': text_overlays['title']},
                    platform=self.format_preset
                )
                self.thumbnail_generated.emit(thumbnail)
            
            # Step 5: Process video with viral optimization
            self.progress.emit(50)
            viral_params = self.ai_processor.get_viral_optimization_params()
            
            # Auto-cut clips based on detected scenes
            processed_clips = []
            for clip, scenes in zip(self.clips, all_scenes):
                subclips = self.scene_detector.auto_cut(clip, scenes)
                processed_clips.extend(subclips)
            
            # Process final video
            self.progress.emit(70)
            final_video = self.video_processor.process_video(
                processed_clips,
                style_params,
                viral_params
            )
            
            # Add text overlays
            self.progress.emit(80)
            final_video = self.add_text_overlays(final_video, text_overlays)
            
            # Export video
            self.progress.emit(90)
            self.video_processor.export_video(
                final_video,
                self.output_path,
                format=os.path.splitext(self.output_path)[1][1:],
                preset=self.format_preset
            )
            
            self.progress.emit(100)
            self.finished.emit(self.output_path)
            
        except Exception as e:
            self.error.emit(str(e))
            
    def add_text_overlays(self, video, text_overlays):
        """Add text overlays to the video."""
        def add_text(frame, t):
            # Add title at the beginning
            if t < 3.0:  # Show title for first 3 seconds
                frame = self.text_generator.create_animated_text(
                    frame, text_overlays['title'], t, 3.0,
                    animation='fade', position='center', style='title'
                )
            
            # Add captions throughout the video
            caption_duration = video.duration / len(text_overlays['captions'])
            caption_index = int(t / caption_duration)
            if caption_index < len(text_overlays['captions']):
                caption_time = t % caption_duration
                frame = self.text_generator.create_animated_text(
                    frame, text_overlays['captions'][caption_index],
                    caption_time, caption_duration,
                    animation='slide', position='bottom', style='caption'
                )
            
            return frame
        
        return video.fl(add_text)
        self.prompt = prompt
        self.output_path = output_path
        self.format_preset = format_preset
        self.ai_processor = AIProcessor()
        self.video_processor = VideoProcessor()

    def run(self):
        try:
            # Analyze prompt
            self.progress.emit(10)
            style_params = self.ai_processor.analyze_prompt(self.prompt)
            
            # Get viral optimization parameters
            self.progress.emit(20)
            viral_params = self.ai_processor.get_viral_optimization_params()
            
            # Process video
            self.progress.emit(40)
            final_video = self.video_processor.process_video(
                self.clips,
                style_params,
                viral_params
            )
            
            # Export video
            self.progress.emit(80)
            self.video_processor.export_video(
                final_video,
                self.output_path,
                format=os.path.splitext(self.output_path)[1][1:],
                preset=self.format_preset
            )
            
            self.progress.emit(100)
            self.finished.emit(self.output_path)
            
        except Exception as e:
            self.error.emit(str(e))

class AIEditPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.clips = []
        self.music_files = []
        self.current_preset = 'youtube'
        self.scene_timestamps = []
        self.text_overlays = {}
        self.thumbnail = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('AI-Edit Pro')
        self.setMinimumSize(1400, 900)
        self.setAcceptDrops(True)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel for controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(400)
        
        # Prompt input section
        prompt_label = QLabel('Enter Your Video Requirements:')
        prompt_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText(
            "Describe your video requirements here...\n\n"
            "Example: Create a cinematic travel video for Instagram\n"
            "with fast-paced transitions, dramatic music,\n"
            "and a duration of 60 seconds."
        )
        
        # Import buttons section
        import_frame = QFrame()
        import_frame.setFrameStyle(QFrame.StyledPanel)
        import_layout = QVBoxLayout(import_frame)
        
        import_label = QLabel('Import Media')
        import_label.setFont(QFont('Arial', 12, QFont.Bold))
        
        self.import_video_btn = QPushButton('Import Video Files')
        self.import_audio_btn = QPushButton('Import Audio Files')
        self.import_image_btn = QPushButton('Import Images')
        
        for btn in [self.import_video_btn, self.import_audio_btn, self.import_image_btn]:
            btn.setMinimumHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 5px;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
        
        # Media list
        self.media_list = QListWidget()
        self.media_list.setStyleSheet("""
            QListWidget {
                background-color: #2C2C2C;
                color: white;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3C3C3C;
            }
            QListWidget::item:selected {
                background-color: #3C3C3C;
            }
        """)
        
        # Export options
        export_frame = QFrame()
        export_frame.setFrameStyle(QFrame.StyledPanel)
        export_layout = QVBoxLayout(export_frame)
        
        export_label = QLabel('Export Settings')
        export_label.setFont(QFont('Arial', 12, QFont.Bold))
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(['YouTube', 'Instagram', 'TikTok'])
        self.format_combo.setStyleSheet("""
            QComboBox {
                background-color: #2C2C2C;
                color: white;
                border-radius: 5px;
                padding: 5px;
                min-height: 30px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        
        # Add widgets to import layout
        import_layout.addWidget(import_label)
        import_layout.addWidget(self.import_video_btn)
        import_layout.addWidget(self.import_audio_btn)
        import_layout.addWidget(self.import_image_btn)
        import_layout.addWidget(self.media_list)
        
        # Add widgets to export layout
        export_layout.addWidget(export_label)
        export_layout.addWidget(self.format_combo)
        
        # Process button
        self.process_btn = QPushButton('Generate Viral Video')
        self.process_btn.setMinimumHeight(50)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        
        # Add widgets to left layout
        left_layout.addWidget(prompt_label)
        left_layout.addWidget(self.prompt_input)
        left_layout.addWidget(import_frame)
        left_layout.addWidget(export_frame)
        left_layout.addWidget(self.process_btn)
        left_layout.addWidget(self.progress_bar)
        
        # Right panel with tabs
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Preview tab
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        
        self.preview_area = QWidget()
        self.preview_area.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                border-radius: 10px;
            }
        """)
        self.preview_area.setMinimumHeight(400)
        
        preview_layout.addWidget(self.preview_area)
        
        # Timeline tab
        timeline_tab = QWidget()
        timeline_layout = QVBoxLayout(timeline_tab)
        
        self.timeline = TimelineWidget()
        timeline_layout.addWidget(self.timeline)
        
        # Thumbnail tab
        thumbnail_tab = QWidget()
        thumbnail_layout = QVBoxLayout(thumbnail_tab)
        
        self.thumbnail_preview = QLabel()
        self.thumbnail_preview.setAlignment(Qt.AlignCenter)
        self.thumbnail_preview.setMinimumHeight(400)
        self.thumbnail_preview.setStyleSheet("""
            QLabel {
                background-color: #1E1E1E;
                border-radius: 10px;
            }
        """)
        
        thumbnail_layout.addWidget(self.thumbnail_preview)
        
        # Add tabs
        self.tab_widget.addTab(preview_tab, "Preview")
        self.tab_widget.addTab(timeline_tab, "Timeline")
        self.tab_widget.addTab(thumbnail_tab, "Thumbnail")
        
        right_layout.addWidget(self.tab_widget)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Connect signals
        self.import_video_btn.clicked.connect(lambda: self.import_files('video'))
        self.import_audio_btn.clicked.connect(lambda: self.import_files('audio'))
        self.import_image_btn.clicked.connect(lambda: self.import_files('image'))
        self.process_btn.clicked.connect(self.process_video)
        self.format_combo.currentTextChanged.connect(self.update_format_preset)
        
        self.show()
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in ['.mp4', '.avi', '.mov', '.wmv']:
                self.add_media_file(file, 'video')
            elif ext in ['.mp3', '.wav', '.m4a']:
                self.add_media_file(file, 'audio')
            elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
                self.add_media_file(file, 'image')
    
    def add_media_file(self, file_path: str, file_type: str):
        base_name = os.path.basename(file_path)
        item_text = f"{file_type.upper()}: {base_name}"
        self.media_list.addItem(item_text)
        
        if file_type == 'video':
            clip = VideoFileClip(file_path)
            self.clips.append(clip)
            
            # Add clip to timeline
            frame = clip.get_frame(0)  # Get first frame for thumbnail
            height = frame.shape[0]
            width = frame.shape[1]
            bytes_per_line = 3 * width
            
            # Convert numpy array to QImage
            q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            self.timeline.add_clip(clip, q_img)
            
        elif file_type == 'audio':
            self.music_files.append(file_path)
            # Add audio waveform to timeline
            self.timeline.set_audio_waveform(file_path)
    
    def update_format_preset(self, text: str):
        self.current_preset = text.lower()
    
    def process_video(self):
        if not self.clips:
            QMessageBox.warning(self, "Error", "Please import at least one video clip.")
            return
        
        prompt = self.prompt_input.toPlainText()
        if not prompt:
            QMessageBox.warning(self, "Error", "Please enter video requirements.")
            return
        
        # Get output path
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Video",
            "",
            "Video Files (*.mp4);;MKV Files (*.mkv);;AVI Files (*.avi);;MOV Files (*.mov)"
        )
        
        if not output_path:
            return
        
        # Disable UI during processing
        self.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Start processing thread
        self.processing_thread = ProcessingThread(
            self.clips,
            prompt,
            output_path,
            self.current_preset
        )
        
        # Connect signals
        self.processing_thread.progress.connect(self.progress_bar.setValue)
        self.processing_thread.finished.connect(self.processing_finished)
        self.processing_thread.error.connect(self.processing_error)
        self.processing_thread.scene_detected.connect(self.handle_scene_detection)
        self.processing_thread.thumbnail_generated.connect(self.handle_thumbnail)
        self.processing_thread.text_generated.connect(self.handle_text_generation)
        
        self.processing_thread.start()
    
    def handle_scene_detection(self, scenes):
        """Handle detected scenes."""
        self.scene_timestamps = scenes
        
        # Clear timeline
        self.timeline.clear()
        
        # Add detected scenes to timeline
        for clip, scenes in zip(self.clips, [scenes]):  # Group scenes by clip
            for start, end in scenes:
                subclip = clip.subclip(start, end)
                frame = subclip.get_frame(0)
                
                # Convert frame to QImage
                height = frame.shape[0]
                width = frame.shape[1]
                bytes_per_line = 3 * width
                q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
                
                self.timeline.add_clip(subclip, q_img)
    
    def handle_thumbnail(self, thumbnail):
        """Handle generated thumbnail."""
        self.thumbnail = thumbnail
        
        # Convert numpy array to QImage
        height = thumbnail.shape[0]
        width = thumbnail.shape[1]
        bytes_per_line = 3 * width
        q_img = QImage(thumbnail.data, width, height, bytes_per_line, QImage.Format_RGB888)
        
        # Create pixmap and scale it to fit the preview area
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(
            self.thumbnail_preview.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        # Display thumbnail
        self.thumbnail_preview.setPixmap(scaled_pixmap)
        self.tab_widget.setCurrentIndex(2)  # Switch to thumbnail tab
    
    def handle_text_generation(self, text_overlays):
        """Handle generated text overlays."""
        self.text_overlays = text_overlays
    
    def processing_finished(self, output_path: str):
        self.setEnabled(True)
        QMessageBox.information(
            self,
            "Success",
            f"Video has been generated and saved to:\n{output_path}"
        )
    
    def processing_error(self, error_msg: str):
        self.setEnabled(True)
        QMessageBox.critical(self, "Error", f"An error occurred:\n{error_msg}")
    
    def import_files(self, file_type: str):
        file_filters = {
            'video': 'Video Files (*.mp4 *.avi *.mov *.wmv)',
            'audio': 'Audio Files (*.mp3 *.wav *.m4a)',
            'image': 'Image Files (*.jpg *.jpeg *.png *.gif)'
        }
        
        files, _ = QFileDialog.getOpenFileNames(
            self,
            f"Select {file_type.capitalize()} Files",
            "",
            file_filters[file_type]
        )
        
        for file in files:
            self.add_media_file(file, file_type)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application-wide stylesheet
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1E1E1E;
        }
        QWidget {
            color: #FFFFFF;
        }
        QLabel {
            color: #FFFFFF;
            margin-bottom: 5px;
        }
        QTextEdit {
            background-color: #2C2C2C;
            border: 2px solid #3C3C3C;
            border-radius: 5px;
            padding: 10px;
            font-size: 11pt;
            color: #FFFFFF;
        }
        QFrame {
            background-color: #2C2C2C;
            border: 1px solid #3C3C3C;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0px;
        }
        QPushButton {
            background-color: #2196F3;
            color: white;
            border-radius: 5px;
            padding: 8px 15px;
            font-size: 11pt;
            border: none;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
        QPushButton:pressed {
            background-color: #0D47A1;
        }
        QProgressBar {
            border: 2px solid #3C3C3C;
            border-radius: 5px;
            text-align: center;
            background-color: #2C2C2C;
            color: white;
        }
        QProgressBar::chunk {
            background-color: #2196F3;
            border-radius: 3px;
        }
        QComboBox {
            background-color: #2C2C2C;
            border: 1px solid #3C3C3C;
            border-radius: 5px;
            padding: 5px;
            min-height: 30px;
            color: white;
        }
        QComboBox::drop-down {
            border: none;
            width: 30px;
        }
        QComboBox::down-arrow {
            image: url(down_arrow.png);
            width: 12px;
            height: 12px;
        }
        QComboBox QAbstractItemView {
            background-color: #2C2C2C;
            border: 1px solid #3C3C3C;
            selection-background-color: #3C3C3C;
            selection-color: white;
        }
        QTabWidget::pane {
            border: 1px solid #3C3C3C;
            background-color: #2C2C2C;
            border-radius: 5px;
        }
        QTabBar::tab {
            background-color: #1E1E1E;
            color: #FFFFFF;
            padding: 8px 15px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            border: 1px solid #3C3C3C;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #2C2C2C;
            border-bottom: none;
        }
        QTabBar::tab:hover {
            background-color: #3C3C3C;
        }
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        QScrollBar:vertical {
            border: none;
            background-color: #2C2C2C;
            width: 10px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background-color: #3C3C3C;
            border-radius: 5px;
            min-height: 20px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            border: none;
            background-color: #2C2C2C;
            height: 10px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background-color: #3C3C3C;
            border-radius: 5px;
            min-width: 20px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        QSplitter::handle {
            background-color: #3C3C3C;
            width: 2px;
        }
        QMessageBox {
            background-color: #2C2C2C;
            color: white;
        }
        QMessageBox QPushButton {
            min-width: 80px;
            min-height: 30px;
        }
    """)
    
    ex = AIEditPro()
    sys.exit(app.exec_())