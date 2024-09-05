import os
import shutil
import whisper
from tempfile import TemporaryDirectory  # Import for temp directory handling
from pydub import AudioSegment, silence
from moviepy.editor import VideoFileClip

from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl
from PySide6.QtGui import QPalette, QColor, QDropEvent, QDragEnterEvent, QClipboard, QDesktopServices
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QVBoxLayout, QWidget, QProgressBar, QTextEdit, QSizePolicy, QHBoxLayout


# Thread to handle the transcription process without freezing the GUI
class TranscriptionThread(QThread):
    progress_signal = Signal(int)
    result_signal = Signal(str)
    log_signal = Signal(str)

    def __init__(self, video_file, parent=None):
        super().__init__(parent)
        self.video_file = video_file

    def run(self):
        transcription_result = self.transcribe_video(self.video_file)
        self.result_signal.emit(transcription_result)
        self.log("Done!")

    def log(self, message):
        self.log_signal.emit(message)

    def extract_audio_from_video(self, video_file, temp_dir):
        self.log("Converting video to audio...")
        video = VideoFileClip(video_file)
        audio_file = os.path.join(temp_dir, "extracted_audio.wav")
        video.audio.write_audiofile(audio_file, codec="pcm_s16le")
        return audio_file

    def split_audio_on_silence_with_timing(self, audio_file, temp_dir, silence_thresh=-40, min_silence_len=700, max_chunk_length=10 * 1000):
        self.log("Splitting audio into chunks...")
        audio = AudioSegment.from_file(audio_file, format="wav")
        chunks = silence.split_on_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh, keep_silence=True)

        if not chunks:
            self.log("No significant silences found. Treating entire audio as one chunk.")
            chunks = [(audio, 0)]

        processed_chunks = []
        start_time = 0
        for chunk in chunks:
            if len(chunk) > max_chunk_length:
                for i in range(0, len(chunk), max_chunk_length):
                    sub_chunk = chunk[i:i + max_chunk_length]
                    processed_chunks.append((sub_chunk, start_time + i))
            else:
                processed_chunks.append((chunk, start_time))
            start_time += len(chunk)

        return processed_chunks

    def transcribe_audio_whisper(self, audio_chunk):
        self.log("Transcribing audio chunk...")
        model = whisper.load_model("base")
        result = model.transcribe(audio_chunk)
        return result['text']

    def transcribe_video(self, video_file):
        # Use a temporary directory to store audio and chunk files
        with TemporaryDirectory() as temp_dir:
            # Extract audio from video
            audio_file = self.extract_audio_from_video(video_file, temp_dir)

            # Split audio into chunks based on silence
            audio_chunks_with_timing = self.split_audio_on_silence_with_timing(audio_file, temp_dir)

            if not audio_chunks_with_timing:
                return "No audio chunks were generated."

            transcription_result = ""

            for i, (chunk, start_time) in enumerate(audio_chunks_with_timing):
                chunk_file = os.path.join(temp_dir, f"chunk_{i}.wav")
                chunk.export(chunk_file, format="wav")
                transcription = self.transcribe_audio_whisper(chunk_file)

                start_time_sec = start_time / 1000.0
                hours = int(start_time_sec // 3600)
                minutes = int((start_time_sec % 3600) // 60)
                seconds = int(start_time_sec % 60)
                timestamp = f"{hours:02}:{minutes:02}:{seconds:02}"

                transcription_result += f"{timestamp} {transcription}\n"

                # Update progress
                self.progress_signal.emit(int((i + 1) / len(audio_chunks_with_timing) * 100))

            return transcription_result


class TranscriptionApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up window
        self.setWindowTitle("Transient - Transcription App")
        self.setGeometry(300, 200, 600, 600)

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Set up dark mode palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(25, 25, 25))  # Main background dark
        palette.setColor(QPalette.WindowText, Qt.white)  # Text color
        palette.setColor(QPalette.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.Button, QColor(255, 255, 255))  # White buttons
        palette.setColor(QPalette.ButtonText, Qt.black)
        self.setPalette(palette)

        # Styling for the window
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: white;
                font-family: Arial, sans-serif;
            }
            QTextEdit {
                font-size: 14px;
                color: white;
                background-color: #2d2d2d;
            }
            QPushButton {
                font-size: 16px;
                padding: 10px 20px;
                color: black;
                background-color: white;
                border-radius: 8px;
                min-width: 120px;
                max-width: 200px;
            }
            QPushButton:hover {
                opacity: 0.7;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.5);
            }
            QPushButton:disabled {
                background-color: #333;
                color: #777;
            }
        """)

        # Layout
        layout = QVBoxLayout()

        # Label
        self.label = QLabel("Select a video file to transcribe (Supports .mp4 and .mov)")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Button to select file
        self.button = QPushButton("Select Video")
        self.button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.button.clicked.connect(self.select_file)
        layout.addWidget(self.button, alignment=Qt.AlignCenter)  # Align to center

        # Button to start transcription
        self.transcribe_button = QPushButton("Transcribe")
        self.transcribe_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.transcribe_button.clicked.connect(self.start_transcription)
        self.transcribe_button.setEnabled(False)  # Disabled until a file is selected
        layout.addWidget(self.transcribe_button, alignment=Qt.AlignCenter)  # Align to center

        # Progress bar
        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        # Transcription display
        self.transcription_display = QTextEdit(self)
        self.transcription_display.setReadOnly(True)
        layout.addWidget(self.transcription_display)

        # Copy button
        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.copy_button.setEnabled(False)  # Disabled until transcription is done
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.copy_button, alignment=Qt.AlignCenter)  # Align to center

        # Label to show "Copied to clipboard" message
        self.copy_status_label = QLabel("")
        layout.addWidget(self.copy_status_label)

        # Log display at the bottom
        self.log_label = QLabel("")
        self.log_label.setWordWrap(True)  # Make logs wrap to multiple lines
        layout.addWidget(self.log_label)

        # Attribution and donation section at the bottom
        bottom_layout = QHBoxLayout()

        # Left side: "Created by Sammoura ❣️" with link
        self.credit_label = QLabel('<a href="https://www.youtube.com/@sammoura-vlogs/videos?sub_confirmation=1" style="color: white;">Created by Sammoura ❣️</a>')
        self.credit_label.setTextFormat(Qt.RichText)
        self.credit_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.credit_label.setOpenExternalLinks(True)
        bottom_layout.addWidget(self.credit_label, alignment=Qt.AlignLeft)

        layout.addLayout(bottom_layout)

        # Main widget setup
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # File to be processed
        self.file_path = None

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.mp4', '.mov')):
                self.file_path = file_path
                self.label.setText(f"Selected file: {os.path.basename(self.file_path)}")
                self.transcribe_button.setEnabled(True)
                break

    def select_file(self):
        # Open file dialog to select a video file
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Video Files (*.mp4 *.mov)")
        if file_dialog.exec():
            self.file_path = file_dialog.selectedFiles()[0]
            self.label.setText(f"Selected file: {os.path.basename(self.file_path)}")
            self.transcribe_button.setEnabled(True)

    def start_transcription(self):
        if not self.file_path:
            return

        # Clear logs
        self.update_log("")
        self.progress_bar.setValue(0)

        # Disable buttons during processing
        self.transcribe_button.setEnabled(False)

        # Start transcription in a separate thread to avoid blocking GUI
        self.transcription_thread = TranscriptionThread(self.file_path)
        self.transcription_thread.progress_signal.connect(self.update_progress)
        self.transcription_thread.result_signal.connect(self.show_transcription)
        self.transcription_thread.log_signal.connect(self.update_log)
        self.transcription_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_log(self, message):
        self.log_label.setText(message)

    def show_transcription(self, result):
        self.transcription_display.setPlainText(result)
        self.copy_button.setEnabled(True)  # Enable the copy button
        self.transcribe_button.setEnabled(True)  # Re-enable the transcribe button
        self.update_log("Transcription completed.")

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.transcription_display.toPlainText())

        # Show "Copied to clipboard!" message
        self.copy_status_label.setText("Copied to clipboard!")

        # Hide the message after 2 seconds
        QTimer.singleShot(2000, lambda: self.copy_status_label.setText(""))

    def open_donation_link(self):
        QDesktopServices.openUrl(QUrl("https://www.example.com/donate"))


# Main entry point
if __name__ == "__main__":
    app = QApplication([])

    window = TranscriptionApp()
    window.show()

    app.exec()
