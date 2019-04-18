import time
import pyaudio  
import wave
import audioop
#define stream chunk   
chunk = 128  

#open a wav format music  
f = wave.open("cache/tmp.wav","rb")  
#instantiate PyAudio  
p = pyaudio.PyAudio()  
#open stream  
stream = p.open(format = p.get_format_from_width(f.getsampwidth()),  
                channels = f.getnchannels(),  
                rate = f.getframerate(),  
                output = True)  
#read data  
data = f.readframes(chunk)  

#play stream  
while data:  
    data = f.readframes(chunk)  
    rms = audioop.rms(data, 2)
    if rms > 3300:
        continue
    stream.write(data)  

#stop stream  
stream.stop_stream()  
stream.close()  

#close PyAudio  
p.terminate()  
