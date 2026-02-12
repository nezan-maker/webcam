import winsound
import cv2 as cv
import paho.mqtt.client as mqtt
import ctypes
import datetime
import os
from cryptography.fernet import Fernet
import threading
import sounddevice as sound
import wavio
import numpy as np
import subprocess
import tempfile
import socket
hostname = socket.gethostname()
ip = socket.gethostbyname_ex(hostname)[2][0]

BROKER_IP = ip
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
TOPIC = "outTopic"
key_str = os.environ["KEY"]
key = key_str.encode()
cipher = Fernet(key)
camera = cv.VideoCapture(0)
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
vid_filename = f"Video_{timestamp}.mp4"
aud_filename = f"Audio_{timestamp}.wav"
vid = cv.VideoWriter_fourcc(*"mp4v")
vid_path = os.path.join("videos", "Soundless", vid_filename)
aud_path = os.path.join("audios", aud_filename)
vid_sound_path = os.path.join("videos", "Sound", vid_filename)
video = cv.VideoWriter(vid_path, vid, 30.0, (640, 480))
recording = True
audio_frames = []
rtmp_url = "rtmp://localhost/hls"
n = 1
stream_key = f"stream{n}"
n += 1
GAIN = 6.0
temp_dir = tempfile.gettempdir()
audio_pipe = os.path.join(temp_dir, "audio_pipe.raw")
video_pipe = os.path.join(temp_dir, "video_pipe.raw")
for pipe in [audio_pipe, video_pipe]:
    if os.path.exists(pipe):
        os.remove(pipe)


def photo_loop():
    global latest_frame
    while True:
        ret, frame = camera.read()
        if ret:
            cv.imshow("Continous", frame)
            video.write(frame)
            latest_frame = frame.copy()
            if cv.waitKey(1) & 0xFF == ord("d"):
                break


GAIN = 7.0


def audio_loop():
    global recording
    fs = 44100
    channels = 1
    with sound.InputStream(samplerate=fs, channels=channels, dtype="float32") as stream:
        while recording:
            data, __ = stream.read(1024)
            data = np.clip(data * GAIN, -1.0, 1.0)
            audio_frames.append(data.copy())


ffmpeg_cmd = [
    r"C:/ffmpeg/ffmpeg/bin/ffmpeg.exe",
    "-y",
    "-i",
    vid_path,
    "-i",
    aud_path,
    "-map",
    "0:v:0",
    "-map",
    "1:a:0",
    "-c:v",
    "libx264",
    "-preset",
    "fast",
    "-c:a",
    "aac",
    "-shortest",
    vid_sound_path,
]


def prevent_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)


def allow_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)


photo_thread = threading.Thread(target=photo_loop)
audio_thread = threading.Thread(target=audio_loop)
photo_thread.start()
audio_thread.start()


def capture_image():
    global latest_frame
    if latest_frame is None:
        print("Image not yet available.")
        return
    success, encoded_image = cv.imencode(".png", latest_frame)
    if not success:
        print("Error encoding !")
    image_bytes = encoded_image.tobytes()
    encrypted_bytes = cipher.encrypt(image_bytes)
    filename = f"Image_{timestamp}.enc"
    with open(os.path.join("images", filename), "wb") as f:
        f.write(encrypted_bytes)
    print(f"File saved : {filename}")


def on_message(client, userdata, msg, properties=None):
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


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(BROKER_IP, 1883, 60, properties=None)
client.subscribe(TOPIC)
prevent_sleep()
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("Program exiting !")
finally:
    recording = False
    allow_sleep()
    photo_thread.join()
    camera.release()
    video.release()
    cv.destroyAllWindows()
    if not audio_frames:
        print("No audio captured")
    audio_thread.join()
    audio_np = np.concatenate(audio_frames, axis=0)
    aud_path = os.path.join("audios", aud_filename)
    wavio.write(aud_path, audio_np, 44100, sampwidth=2, scale=True)
    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print("Audio and Video saved!")
    except subprocess.CalledProcessError as e:
        print("Error in creating complete video", e)
    finally:
        print("Thank you for keeping your trust in us")
