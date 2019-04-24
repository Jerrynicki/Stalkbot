from gtts import gTTS
import time
import subprocess

def download(to_say, ffmpeg_executable):
    tts = gTTS(to_say, lang="de")
    tts.save("cache/tmp.mp3")

    subprocess.call([ffmpeg_executable, "-y", "-i", "cache/tmp.mp3", "-af", "volume=-5dB", "cache/tmp.wav"])
