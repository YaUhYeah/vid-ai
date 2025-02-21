import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QTextEdit, QLabel,
                           QFileDialog, QProgressBar, QFrame, QComboBox,
                           QListWidget, QMessageBox)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QDragEnterEvent, QDropEvent
from moviepy.editor import VideoFileClip
from .ai_processor import AIProcessor
from .video_processor import VideoProcessor

class ProcessingThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, clips, prompt, output_path, format_preset):
        super().__init__()
        self.clips = clips
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
        self.initUI()

    def initUI(self):
        self.setWindowTitle('AI-Edit Pro')
        self.setMinimumSize(1200, 800)
        self.setAcceptDrops(True)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
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
        
        # Right panel for preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        preview_label = QLabel('Preview')
        preview_label.setFont(QFont('Arial', 12, QFont.Bold))
        
        self.preview_area = QWidget()
        self.preview_area.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                border-radius: 10px;
            }
        """)
        self.preview_area.setMinimumHeight(400)
        
        right_layout.addWidget(preview_label)
        right_layout.addWidget(self.preview_area)
        
        # Add panels to main layout
        layout.addWidget(left_panel)
        layout.addWidget(right_panel, stretch=2)
        
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
            self.clips.append(VideoFileClip(file_path))
        elif file_type == 'audio':
            self.music_files.append(file_path)
    
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
        
        self.processing_thread.progress.connect(self.progress_bar.setValue)
        self.processing_thread.finished.connect(self.processing_finished)
        self.processing_thread.error.connect(self.processing_error)
        
        self.processing_thread.start()
    
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
        # TODO: Implement video processing logic
        prompt = self.prompt_input.toPlainText()
        print("Processing video with prompt:", prompt)
        
        # Simulate progress
        self.progress_bar.setValue(50)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application-wide stylesheet
    app.setStyleSheet("""
        QMainWindow {
            background-color: #F5F5F5;
        }
        QLabel {
            color: #333333;
            margin-bottom: 5px;
        }
        QTextEdit {
            background-color: white;
            border: 2px solid #CCCCCC;
            border-radius: 5px;
            padding: 10px;
            font-size: 11pt;
        }
        QFrame {
            background-color: white;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0px;
        }
    """)
    
    ex = AIEditPro()
    sys.exit(app.exec_())