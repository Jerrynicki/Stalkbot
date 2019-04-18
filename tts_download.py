from gtts import gTTS
import time
import os
import sys

to_say = sys.argv[1]

tts = gTTS(to_say, lang="de")
tts.save("cache/tmp.mp3")

os.system("ffmpeg -y -i cache/tmp.mp3 -af \"volume=-5dB\" cache/tmp.wav")
# -af \"volume=15dB\"
