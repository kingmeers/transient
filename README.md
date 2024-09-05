# Transient - YouTube Video Timestamp Generator

**Transient** is a simple desktop application that helps you generate video timestamps for YouTube descriptions. You can drop any `.mp4` or `.mov` video into the app, and it will convert the audio to text and provide timestamps that you can copy directly into your YouTube video description.

## Features

- **Drag and drop**: Just drag your video file into the app and get started.
- **Supports MP4 and MOV** formats.
- **Timestamps and transcription** for easy copy-paste into YouTube descriptions.
- **Dark mode GUI** with a simple interface.
- **Works offline**.

## How it Works

1. You select or drag a video file into the app.
2. The app extracts the audio from the video.
3. The audio is split into chunks using silence detection.
4. Each chunk is transcribed using the Whisper model by OpenAI.
5. Timestamps and transcriptions are generated and displayed in the app.
6. You can copy the generated text to your clipboard to use in YouTube descriptions.

## Installation

### Requirements

- Python 3.10+
- `whisper` by OpenAI
- Required Python packages listed below

### Step-by-Step Build Instructions

#### 1. Clone or Download this Repository

```bash
git clone https://github.com/your-repo/transient
cd transient
```

#### 2. Create a Python Virtual Environment (Recommended)

To avoid package conflicts, it's best to use a virtual environment.

```bash
python3 -m venv env
source env/bin/activate  # On Windows use 'env\Scripts\activate'
```

#### 3. Install Required Dependencies

Run the following command to install the necessary Python packages:

```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:

- `openai-whisper`
- `pydub`
- `PySide6`
- `moviepy`
- `tqdm`

#### 4. Running the App

To launch **Transient**, use the following command:

```bash
python transient.py
```

This will open the GUI window where you can drag and drop your video or select a video manually.

#### 5. Packaging the App (Optional)

If you'd like to package **Transient** into an executable for distribution:

1. **For macOS**:
   Use PyInstaller to create a `.app` file:

   ```bash
   pyinstaller --windowed --icon=t.icns transient.spec
   ```

2. **For Windows**:
   Use PyInstaller to create an `.exe` file:

   ```bash
   pyinstaller --windowed --onefile --icon=icon.ico transient.spec
   ```

Both methods will generate an executable in the `dist` folder.

## Using Transient

1. **Select or Drop a Video**: Click on the "Select Video" button or drag a `.mp4` or `.mov` file into the app window.
2. **Click Transcribe**: After selecting your file, click "Transcribe."
3. **Copy Timestamps**: Once the transcription is complete, copy the timestamps and text to your clipboard by clicking "Copy to Clipboard."
4. **Paste in YouTube**: Paste the copied timestamps directly into your YouTube video description.

## Example Output

Here's an example of what the generated timestamps will look like:

```
00:00 Introduction to Transient
00:45 Features of the app
01:30 How to install Transient
02:15 How to use Transient
...
```

## Contributing

Feel free to submit pull requests or report issues if you find any bugs or want to add new features.
