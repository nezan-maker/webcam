import winsound
import cv2 as cv
import paho.mqtt.client as mqtt
import ctypes
import datetime
import os
from cryptography.fernet import Fernet
import threading
import wavio
import numpy as np
import subprocess
import tempfile
import atexit
import tempfile
import socket

WIDTH = 640
HEIGHT = 480
FPS = 30
AUDIO_RATE = 44100
AUDIO_CHANNELS = 1
RTMP_URL = "rtsp://localhost:8554/stream1"
TOPIC = "outTopic"
FFMPEG = r"C:/ffmpeg/ffmpeg/bin/ffmpeg.exe"
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
BLOCKSIZE = 1024
hostname = socket.gethostname()
ip = socket.gethostbyname_ex(hostname)[2][0]

BROKER_IP = ip
def prevent_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    )
def allow_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS
    )
key_str = os.environ['KEY']
key = key_str.encode()
cipher = Fernet(key)

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
video_dir = "videos/Sound"
os.makedirs(video_dir,exist_ok=True)
image_dir = "images"
os.makedirs(image_dir,exist_ok=True)

vid_path = os.path.join(video_dir, f"Video_{timestamp}.mp4")
image_path = os.path.join(image_dir,f"Image_{timestamp}.enc")

camera = cv.VideoCapture(0)
camera.set(cv.CAP_PROP_FRAME_WIDTH,WIDTH)
camera.set(cv.CAP_PROP_FRAME_HEIGHT,HEIGHT)
camera.set(cv.CAP_PROP_FPS,FPS)
latest_frame = None
running = True

ffmpeg_cmd = [
    FFMPEG,
    "-f", "rawvideo",
    "-pix_fmt", "bgr24",
    "-r", str(FPS),
    "-s", f"{WIDTH}x{HEIGHT}",
    "-i", "pipe:0",

    "-f", "dshow",
    "-i", r"audio=Microphone Array (Intel® Smart Sound Technology for Digital Microphones)",

    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-tune", "zerolatency",
    "-pix_fmt", "yuv420p",
    "-b:v", "2500k",

    "-c:a", "aac",
    "-b:a", "128k",

    "-map", "0:v", "-map", "1:a", "-f", "rtsp", RTMP_URL,
    # 
]

ffmpeg_proc = subprocess.Popen(
    ffmpeg_cmd,
    stdin=subprocess.PIPE,
    stderr=subprocess.PIPE
)
video_fd = ffmpeg_proc.stdin
def video_loop():
    global latest_frame
    
    while running:
        ret,frame = camera.read()
        if not ret:
            print("Error In Camera capture")
            break
        latest_frame = frame.copy()
        cv.imshow("Live Preview",frame)
        try:
            video_fd.write(frame.tobytes())
        except BrokenPipeError:
            print("FFmpeg closed the pipe")
        except OSError as e:
            print("OSError:", e)
        if cv.waitKey(1) & 0xff == ord('d'):
            break
            
def capture_image():
    if latest_frame is None:
        print("Image not ready yet")
        return
    success,encoded = cv.imencode('.png',latest_frame)
    if not success:
        return
    image_bytes = encoded.tobytes()
    encrypted_bytes = cipher.encrypt(image_bytes)
    with open(image_path,"wb") as f:
        f.write(encrypted_bytes)
    print(f"File saved as {image_path}")
def on_message(client,userdata,msg,properties=None):
    message = msg.payload.decode()
    print(f"R: {message}")
    try:
        distance = float(message.split(":")[1].replace("cm", "").strip())
        if distance < 50:
            winsound.PlaySound(
                "buzzer_clip.wav", winsound.SND_FILENAME | winsound.SND_ASYNC
            )
            print("Object detected! Capturing image")
            capture_image()

    except Exception as e:
        print("Parse Error", e)
def read_ffmpeg_errors():
    for line in ffmpeg_proc.stderr:
        print(line)
threading.Thread(target=read_ffmpeg_errors,daemon=True).start()    
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(BROKER_IP, 1883, 60, properties=None)
client.subscribe(TOPIC)
prevent_sleep()
def cleanup():
    global running
    running = False
    allow_sleep()
    
    
    try:
        video_thread.join()
        camera.release()
        cv.destroyAllWindows()
    except:
        pass
    try:
        video_fd.close()
    except:
        pass
    try:
        ffmpeg_proc.terminate()
        ffmpeg_proc.wait(5)
    except:
        ffmpeg_proc.kill()
atexit.register(cleanup)
prevent_sleep()
video_thread = threading.Thread(target=video_loop)
video_thread.start()
try:
    client.loop_forever()
except KeyboardInterrupt:
    pass
finally:
    cleanup()
        
        
    
        
    
    