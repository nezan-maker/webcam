# Webcam Surveillance System

A Python-based intelligent webcam surveillance and streaming system with object detection capabilities, encrypted image storage, and MQTT-based monitoring.

## Overview

This project provides a comprehensive solution for capturing, processing, and streaming video and audio from a webcam with integrated object detection alerts. The system uses MQTT for inter-device communication and encrypts captured images for security.

## Features

- **Live Video Capture**: Real-time video recording from webcam at 30 FPS (640x480 resolution)
- **Audio Recording**: High-quality audio capture at 44.1 kHz mono
- **Object Detection Alerts**: MQTT-based distance monitoring with audio alerts via buzzer
- **Encrypted Storage**: Images are encrypted using Fernet encryption before storage
- **Video Streaming**: Support for RTSP streaming to media servers
- **Dual Recording Modes**:
  - Basic recording with separate video and audio files
  - Streaming mode with live RTSP output
- **Sleep Prevention**: Windows sleep mode prevention during active monitoring
- **Secure Key Management**: Uses environment variables for encryption keys

## Project Structure

```
.
├── main.py              # Primary capture and recording script
├── streaming.py         # Live streaming with RTSP output
├── decoder.py          # Utility to decrypt and view saved images
├── buzzer_clip.wav     # Alert sound for object detection
├── real_name.wav       # Audio file (purpose: context dependent)
├── renewed.wav         # Audio file (purpose: context dependent)
└── README.md           # This file
```

## System Requirements

- **Python 3.7+**
- **Windows OS** (uses Windows-specific APIs for sleep prevention)
- **FFmpeg**: Required for video/audio processing
  - Location: `C:/ffmpeg/ffmpeg/bin/ffmpeg.exe` (configurable)
- **Webcam**: Connected and accessible
- **Microphone**: For audio capture
- **MQTT Broker**: Running on local network

### Python Dependencies

```
opencv-python (cv2)
paho-mqtt
cryptography
numpy
sounddevice
wavio
```

Install dependencies:
```bash
pip install opencv-python paho-mqtt cryptography numpy sounddevice wavio
```

## Configuration

### Environment Variables

Set the following environment variable before running:
```bash
set KEY=<your-fernet-encryption-key>
```

Generate a Fernet key:
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())
```

### Configuration Parameters (in code)

**main.py:**
- `BROKER_IP`: MQTT broker address (auto-detected as local IP)
- `TOPIC`: MQTT topic to subscribe to (default: "outTopic")
- `GAIN`: Audio gain multiplier (default: 7.0)
- `FPS`: Video frame rate (default: 30)
- `WIDTH/HEIGHT`: Video resolution (default: 640x480)

**streaming.py:**
- `RTMP_URL`: RTSP server endpoint (default: "rtsp://localhost:8554/stream1")
- `AUDIO_RATE`: Audio sampling rate (default: 44100 Hz)
- Similar configuration parameters as main.py

### FFmpeg Setup

Windows example:
```bash
# Install FFmpeg or set the path in the scripts
ffmpeg_path = r"C:/ffmpeg/ffmpeg/bin/ffmpeg.exe"
```

## Usage

### Basic Recording Mode

Captures video and audio separately, then combines them using FFmpeg:

```bash
python main.py
```

**Output:**
- `videos/Soundless/Video_<timestamp>.mp4` - Silent video file
- `audios/Audio_<timestamp>.wav` - Audio file
- `videos/Sound/Video_<timestamp>.mp4` - Combined video with audio
- `images/Image_<timestamp>.enc` - Encrypted captured images

**Exit:**
Press 'd' key in the video window to stop recording, or use `Ctrl+C`.

### Streaming Mode

Streams live video to an RTSP server:

```bash
python streaming.py
```

**Output:**
- Live stream to configured RTSP URL
- Encrypted images saved on object detection

**Exit:**
Press 'd' key in the video window or use `Ctrl+C`.

### Decrypt and View Images

View encrypted images captured during operation:

```bash
python decoder.py
# Enter the encrypted filename when prompted (e.g., Image_2024-01-15_10-30-45.enc)
```

Press 'd' key to close the image viewer.

## How It Works

### Object Detection Flow

1. System subscribes to MQTT topic for distance measurements
2. When message is received with format `distance:XXcm`
3. If distance < 50cm, an object is detected
4. Audio alert (buzzer) is played
5. Current video frame is captured and encrypted
6. Encrypted image is saved to disk

### MQTT Message Format

Expected format:
```
distance:45cm
distance:120cm
```

### Video Processing

**main.py**: Uses FFmpeg to merge video and audio:
```bash
ffmpeg -i video.mp4 -i audio.wav -c:v libx264 -c:a aac -shortest output.mp4
```

**streaming.py**: Pipes raw video frames directly to FFmpeg for RTSP streaming.

## Security Features

- **Fernet Encryption**: All saved images are encrypted with a symmetric key
- **Key Management**: Encryption key stored in environment variables (not in code)
- **Secure File Handling**: Encrypted files use `.enc` extension

## Directory Structure Expected

Create these directories before running:

```
📁 videos/
  📁 Soundless/    # Silent video files
  📁 Sound/        # Combined video with audio
📁 audios/         # Audio files
📁 images/         # Encrypted images
```

Or they will be created automatically by the scripts.

## Troubleshooting

### FFmpeg Not Found
- Verify FFmpeg installation path matches the script configuration
- Update the path in the code to your FFmpeg location

### MQTT Connection Issues
- Ensure MQTT broker is running and accessible
- Check if broker IP address is correctly identified
- Verify network connectivity between system and broker

### Audio Issues
- Ensure microphone is properly connected and enabled
- Check Windows audio input settings
- Verify sounddevice package is installed: `pip install sounddevice`

### Video Codec Issues
- Install FFmpeg with libx264 codec support
- For RTSP streaming, verify RTSP server is running (e.g., mediamtx)

## Limitations

- **Windows Only**: Uses Windows-specific APIs (`ctypes.windll`)
- **Fixed Paths**: FFmpeg path is hardcoded; requires modification for other systems
- **Single Camera**: Configured for single webcam capture
- **Fixed Resolution**: Resolution is preset to 640x480

## Future Enhancements

- Cross-platform support (Linux, macOS)
- Multi-camera support
- Configurable resolution and frame rates
- Database integration for image metadata
- Web UI for monitoring
- Email/Webhook alerts
- Motion detection algorithms
- Cloud storage integration

## License

Not specified in this project.

## Author

nezan-maker

## Support

For issues or questions, please refer to the project repository.
