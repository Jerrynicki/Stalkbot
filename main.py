import discord
from discord.ext import commands
import json
import os
import logging
import subprocess
import asyncio
import threading
import socket
import time
import cv2
import numpy
from PIL import Image, ImageFilter
import keyboard as keyboard_module
import mouse
import sum_process_resources
import urllib.request
import urllib.parse
import json
import random
import tkinter as tk
import pyaudio
import wave
import audioop
import pyautogui

logging.basicConfig(level=logging.INFO)

sound_playing = False

repeat_emoji = "\U0001F501"
play_emoji = "\U000025B6"
white_check_mark_emoji = "\U00002611"
stop_sign_emoji = "\U0001F6D1"
negative_squared_cross_mark_emoji = "\U0000274E"
no_entry_emoji = "\U000026D4"
outbox_tray_emoji = "\U0001F4E4"
no_bell_emoji = "\U0001F515"

config = json.load(open("config.json", "r"))

blacklist = config["blacklist"]
TOKEN = config["token"]

ueberwachung_standard = {"global": True, "tts": True, "screenshot": True, "webcam": True, "proc": True, "play": True, "cursor": True, "keyboard": True}
try:
    ueberwachung_from_file = json.load(open("ueberwachung_retain.json"))
    if ueberwachung_from_file.keys() == ueberwachung_standard.keys():
        ueberwachung = ueberwachung_from_file
    else:
        print("Deine Einstellungen zu den Features des Bots sind von einer veralteten Version! Sie wurden auf die Standardeinstellungen zurückgesetzt.")
        ueberwachung = ueberwachung_standard
except:
    ueberwachung = ueberwachung_standard

bot = commands.Bot(command_prefix=config["prefix"], description="jejei")

if not os.path.isdir("cache"):
    os.mkdir("cache")

def notification(action, ctx):
    notify_config = config["notifications"]["text"]
    subprocess.call(["notify-send", "-t", config["notifications"]["duration"], notify_config.replace("$AUTHOR", ctx.message.author.name).replace("$SERVER", ctx.message.server.name).replace("$CHANNEL", "#" + ctx.message.channel.name).replace("$ACTION", action)])

def play_file(file, earrape_protection=False, timeout=False):
    chunk = 128
    f = wave.open(file, "rb")

    if timeout == "auto":
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        timeout = duration + 1
        start_time = time.time()
    
    elif timeout != False:
        start_time = time.time()

    p = pyaudio.PyAudio()  
    stream = p.open(format = p.get_format_from_width(f.getsampwidth()), channels = f.getnchannels(), rate = f.getframerate(), output = True)
    data = f.readframes(chunk)

    timed_out = False
    while data:
        data = f.readframes(chunk)
        rms = audioop.rms(data, 2)
        if earrape_protection and rms > 3300:
            continue
        stream.write(data)
        if time.time() > start_time + timeout:
            timed_out = True
            break

    stream.stop_stream()  
    stream.close()  

    p.terminate()

    if timed_out:
        raise TimeoutError

@bot.event
async def on_ready():
    print("Logged in as " + bot.user.name + "#" + bot.user.discriminator)
    await asyncio.sleep(5)
    while True:
        await bot.change_presence(status=discord.Status.online, game=discord.Game(name=config["status"]))
        await asyncio.sleep(20)


@bot.command(pass_context=True, aliases=["tts"])
async def say(ctx, *message):
    """Spielt eine Nachricht per TTS auf meinem PC ab."""

    global sound_playing
    message = " ".join(message)

    if not ueberwachung["tts"]:
        await bot.add_reaction(ctx.message, no_bell_emoji)
        return

    if sound_playing:
        await bot.add_reaction(ctx.message, no_entry_emoji)
        return

    if ctx.message.author.id in blacklist:
        await bot.say(ctx.message.author.mention + " hurensohn bist geblacklistet weil du hurensohn bist\nfick dich")
        return

    try:
        await bot.add_reaction(ctx.message, repeat_emoji)

        proc = subprocess.Popen(["python3", "tts_download.py",
                                 ctx.message.author.name + "sagt: " + message])
        proc.wait(timeout=10)
        await bot.remove_reaction(ctx.message, repeat_emoji, ctx.message.server.me)
        await bot.add_reaction(ctx.message, play_emoji)

        notification("TTS", ctx)

        try:
            sound_playing = True
            play_file("cache/tmp.wav", timeout=20)
            await bot.remove_reaction(ctx.message, play_emoji, ctx.message.server.me)
            await bot.add_reaction(ctx.message, white_check_mark_emoji)
        except:
            await bot.remove_reaction(ctx.message, play_emoji, ctx.message.server.me)
            await bot.add_reaction(ctx.message, stop_sign_emoji)
    except:
        await bot.remove_reaction(ctx.message, play_emoji, ctx.message.server.me)
        await bot.add_reaction(ctx.message, negative_squared_cross_mark_emoji)

    proc.terminate()
    sound_playing = False


image_lock = False
image_countdown = 0


@bot.command(pass_context=True, aliases=["cam", "wc"])
async def webcam(ctx):
    global image_lock
    global image_countdown

    if not ueberwachung["webcam"]:
        await bot.add_reaction(ctx.message, no_bell_emoji)
        return

    if image_lock or image_countdown > time.time() or not ueberwachung:
        await bot.add_reaction(ctx.message, negative_squared_cross_mark_emoji)
        return

    if ctx.message.author.id in blacklist:
        await bot.say(ctx.message.author.mention + " hurensohn bist geblacklistet weil du hurensohn bist\nfick dich")
        return

    await bot.add_reaction(ctx.message, repeat_emoji)

    image_lock = True

    try:
        play_file("warning_sound.wav", timeout="auto")
        notification("Webcam", ctx)

        cam = cv2.VideoCapture(0) 
        test_success, test_image = cam.read()
        start_wait = time.time()
        failed_reads = 0
        while time.time() < start_wait + int(config["webcamdelay"]) or test_success is False: 
            test_success, test_image = cam.read() 
            if test_success is False:
                failed_reads += 1
            if failed_reads >= 3:
                raise Exception("Zu viele Frames nicht gelesen. Bitte versuche es noch einmal.")

            time.sleep(1/5)

        print(cam.isOpened())
        success, image = cam.read()
        cv2.imwrite("cache/image.png", image)
        cam.release()

        img = Image.open("cache/image.png")
        img.save("cache/image.jpg", quality=80)

        await bot.send_file(ctx.message.channel, "cache/image.jpg")
        await bot.remove_reaction(ctx.message, repeat_emoji, ctx.message.server.me)
    except Exception as exc:
        await bot.say("`" + str(exc) + "`")

    finally:
        image_lock = False
        image_countdown = time.time() + 15


screenshot_lock = False
screenshot_countdown = 0


@bot.command(pass_context=True, aliases=["scr", "sc", "ss"])
async def screenshot(ctx):
    global screenshot_lock
    global screenshot_countdown

    if not ueberwachung["screenshot"]:
        await bot.add_reaction(ctx.message, no_bell_emoji)
        return
    
    if screenshot_lock or screenshot_countdown > time.time():
        await bot.add_reaction(ctx.message, negative_squared_cross_mark_emoji)
        return

    if ctx.message.author.id in blacklist:
        await bot.say(ctx.message.author.mention + " hurensohn bist geblacklistet weil du hurensohn bist\nfick dich")
        return

    try:
        screenshot_lock = True

        play_file("warning_sound.wav", timeout="auto")
        notification("Screenshot", ctx)

        await bot.add_reaction(ctx.message, repeat_emoji)

        # screenshot = screenshot_gtk()
        subprocess.call(["scrot", "cache/screenshot.png"])
        screenshot = Image.open("cache/screenshot.png")
        screenshot = screenshot.filter(ImageFilter.GaussianBlur(radius=3))
        screenshot.save("cache/screenshot_blurred.jpg", quality=80)

        await bot.send_file(ctx.message.channel, "cache/screenshot_blurred.jpg")
        await bot.remove_reaction(ctx.message, repeat_emoji, ctx.message.server.me)
    except Exception as exc:
        await bot.say("`" + str(exc) + "`")

    finally:
        screenshot_lock = False
        screenshot_countdown = time.time() + 15


@bot.command(pass_context=True)
async def proc(ctx, *arg):
    arg = " ".join(arg)

    if not ueberwachung["proc"]:
        await bot.add_reaction(ctx.message, no_bell_emoji)
        return

    if ctx.message.author.id in blacklist:
        await bot.say(ctx.message.author.mention + " hurensohn bist geblacklistet weil du hurensohn bist\nfick dich")
        return

    if not arg or arg not in ("cpu", "ram", "focused"):
        await bot.say("Bitte gebe als Argument entweder `cpu`, `ram` oder `focused` an.")
        return
  
    play_file("warning_sound.wav", timeout="auto")
       
    notification("Proc" + arg.upper(), ctx)

    if arg == "cpu":
        sum_process_resources.sum_process_resources("cpu")
        await bot.say("Top 6 Prozesse nach CPU-Nutzung:\n" + open("cache/proc.txt", "r").read())

    elif arg == "ram":
        sum_process_resources.sum_process_resources("ram")
        await bot.say("Top 6 Prozesse nach RAM-Nutzung:\n" + open("cache/proc.txt", "r").read())

    elif arg == "focused":
        os.system("xdotool getwindowfocus getwindowname > cache/xdotool.txt")
        os.system("xdotool getwindowfocus getwindowgeometry >> cache/xdotool.txt")
        with open("cache/xdotool.txt", "r") as file:
            info = file.read() 

        await bot.say(info)



@bot.command(pass_context=True)
async def miku(ctx):
    """Miku-Command für Sukeldukel uwu"""


@bot.command(pass_context=True)
async def play(ctx, *url):
    """Spielt eine beliebige (mit FFmpeg kompatible) Audiodatei ab"""

    global sound_playing

    if not ueberwachung["play"]:
        await bot.add_reaction(ctx.message, no_bell_emoji)
        return

    if ctx.message.author.id in blacklist:
        await bot.say(ctx.message.author.mention + " hurensohn bist geblacklistet weil du hurensohn bist\nfick dich")
        return

    if url:
        url = " ".join(url)
        if len(url) > 0:
            ctx.message.attachments = [{"url": url}]

    if sound_playing:
        await bot.add_reaction(ctx.message, no_entry_emoji)
        return

    try:
        print(ctx.message.attachments)


        play_file("warning_sound.wav", timeout="auto")
        notification("Play " + ctx.message.attachments[0]["url"].split("/")[-1], ctx)

        await bot.add_reaction(ctx.message, repeat_emoji)
        req = urllib.request.Request(url=ctx.message.attachments[0]["url"], headers={
                                     "User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req).read()
        with open("cache/tmp." + ctx.message.attachments[0]["url"].split(".")[-1], "wb") as file:
            file.write(resp)

        subprocess.call(["ffmpeg", "-y", "-i", "cache/tmp." + ctx.message.attachments[0]
                         ["url"].split(".")[-1], "-af", "volume=-25dB", "cache/tmp.wav"])

        await bot.remove_reaction(ctx.message, repeat_emoji, ctx.message.server.me)
        await bot.add_reaction(ctx.message, play_emoji)
        try:
            sound_playing = True 
            play_file("cache/tmp.wav", timeout=20, earrape_protection=True) 
            await bot.remove_reaction(ctx.message, play_emoji, ctx.message.server.me)
            await bot.add_reaction(ctx.message, white_check_mark_emoji)
        except Exception as exc:
            await bot.remove_reaction(ctx.message, play_emoji, ctx.message.server.me)
            await bot.add_reaction(ctx.message, stop_sign_emoji)
    except Exception as exc:
        await bot.remove_reaction(ctx.message, play_emoji, ctx.message.server.me)
        await bot.add_reaction(ctx.message, negative_squared_cross_mark_emoji)
        print(exc)

    sound_playing = False
    os.unlink("cache/tmp." + ctx.message.attachments[0]["url"].split(".")[-1])

@bot.command(pass_context=True)
async def cursor(ctx, *coordinates):
    if ctx.message.author.id in blacklist:
        await bot.say(ctx.message.author.mention + " hurensohn bist geblacklistet weil du hurensohn bist\nfick dich")
        return
 
    if not ueberwachung["cursor"]:
        await bot.add_reaction(ctx.message, no_bell_emoji)
        return

    if len(coordinates) >= 2:
        x, y = coordinates[0], coordinates[1]
    else:
        screen = pyautogui.size()
        x, y = random.randint(0, screen[0]), random.randint(0, screen[1])

    play_file("warning_sound.wav", timeout="auto")
    notification("Cursor: " + str(x) + "x" + str(y), ctx)

    mouse.move(x, y, duration=0.5)
    await bot.add_reaction(ctx.message, white_check_mark_emoji)

@bot.command(pass_context=True)
async def keyboard(ctx, *text):
    text = " ".join(text)

    if ctx.message.author.id in blacklist:
        await bot.say(ctx.message.author.mention + " hurensohn bist geblacklistet weil du hurensohn bist\nfick dich")
        return
    
    if not ueberwachung["keyboard"]:
        await bot.add_reaction(ctx.message, no_bell_emoji)
        return

    if len(text) > 50:
        await bot.add_reaction(ctx.message, negative_squared_cross_mark_emoji)
        await bot.say("Der Text ist zu lang! (max. 50 Zeichen)")
        return

    play_file("warning_sound.wav", timeout="auto")
    notification("Keyboard: " + text, ctx)

    keyboard_module.write(text, delay=0.05, exact=True)
    await bot.add_reaction(ctx.message, white_check_mark_emoji)

@bot.command(pass_context=True)
async def folder(ctx):
    try:
        source = config["folder"]
    except KeyError:
        await bot.say("Es wurde kein Ordner in der Config angegeben.")
    else:
        valid_file = False
        files = os.listdir(source)
        while not valid_file:
            raw_file = random.choice(files)
            file = source + "/" + raw_file
            if os.path.isfile(file) and os.path.getsize(file) < 8*1024**2:
                valid_file = True
            else:
                valid_file = False

        notification("Folder: " + raw_file, ctx)
        await bot.add_reaction(ctx.message, outbox_tray_emoji)
        await bot.send_file(ctx.message.channel, file)
        await bot.remove_reaction(ctx.message, outbox_tray_emoji, ctx.message.server.me)


@bot.command()
async def emojihelp():
    await bot.say("Emoji-Reaktionen und ihre Bedeutungen:\n" +
                  repeat_emoji + " Audiodatei wird generiert\n" +
                  play_emoji + " Nachricht wird abgespielt\n" +
                  white_check_mark_emoji + " Nachricht erfolgreich abgespielt\n" +
                  stop_sign_emoji + " Nachricht wurde abgebrochen (max. 20 Sekunden)\n" +
                  negative_squared_cross_mark_emoji + " Ein Fehler ist aufgetreten\n" +
                  no_entry_emoji + " Eine TTS-Nachricht wird gerade schon abgespielt")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("!!"):
        message.content = "jer!" + message.content[2:]

    await bot.process_commands(message)


def toggle_überwachung():
    global ueberwachung
    root = tk.Tk()
    root.title("Stalkbot Überwachung Control-Panel")
    # TODO: diesen code schöner machen

    def toggle_tts():
        if ueberwachung["tts"]:
            ueberwachung["tts"] = False
        else:
            ueberwachung["tts"] = True

    def toggle_screenshot():
        if ueberwachung["screenshot"]:
            ueberwachung["screenshot"] = False
        else:
            ueberwachung["screenshot"] = True

    def toggle_webcam():
        if ueberwachung["webcam"]:
            ueberwachung["webcam"] = False
        else:
            ueberwachung["webcam"] = True

    def toggle_proc():
        if ueberwachung["proc"]:
            ueberwachung["proc"] = False
        else:
            ueberwachung["proc"] = True

    def toggle_play():
        if ueberwachung["play"]:
            ueberwachung["play"] = False
        else:
            ueberwachung["play"] = True
    
    def toggle_cursor():
        if ueberwachung["cursor"]:
            ueberwachung["cursor"] = False
        else:
            ueberwachung["cursor"] = True
    
    def toggle_keyboard():
        if ueberwachung["keyboard"]:
            ueberwachung["keyboard"] = False
        else:
            ueberwachung["keyboard"] = True

    tts_bt = tk.Button(root, text="TTS: " + str(ueberwachung["tts"]), command=toggle_tts, font=("Helvetica", 16))
    scr_bt = tk.Button(root, text="Screenshot: " + str(ueberwachung["screenshot"]), command=toggle_screenshot, font=("Helvetica", 16))
    webcam_bt = tk.Button(root, text="Webcam: " + str(ueberwachung["webcam"]), command=toggle_webcam, font=("Helvetica", 16))
    proc_bt = tk.Button(root, text="Prozessliste: " + str(ueberwachung["proc"]), command=toggle_proc, font=("Helvetica", 16))
    play_bt = tk.Button(root, text="Play: " + str(ueberwachung["play"]), command=toggle_play, font=("Helvetica", 16))
    cursor_bt = tk.Button(root, text="Cursor: " + str(ueberwachung["cursor"]), command=toggle_cursor, font=("Helvetica", 16))
    keyboard_bt = tk.Button(root, text="Tastatur: " + str(ueberwachung["keyboard"]), command=toggle_keyboard, font=("Helvetica", 16))

    done_bt = tk.Button(root, text="Fertig", command=root.destroy, font=("Helvetica", 14))

    tts_bt.pack()
    scr_bt.pack()
    webcam_bt.pack()
    proc_bt.pack()
    play_bt.pack()
    cursor_bt.pack()
    keyboard_bt.pack()
    done_bt.pack()
    while True:
        try:
            tts_bt.config(text="TTS: " + str(ueberwachung["tts"]))
            scr_bt.config(text="Screenshot: " + str(ueberwachung["screenshot"]))
            webcam_bt.config(text="Webcam: " + str(ueberwachung["webcam"]))
            proc_bt.config(text="Prozessliste: " + str(ueberwachung["proc"]))
            play_bt.config(text="Play: " + str(ueberwachung["play"]))
            cursor_bt.config(text="Cursor: " + str(ueberwachung["cursor"]))
            keyboard_bt.config(text="Tastatur: " + str(ueberwachung["keyboard"]))
            root.update()
            time.sleep(1/30)
        except:
            break
    json.dump(ueberwachung, open("ueberwachung_retain.json", "w"))

if not "control_panel_hotkey" in config and "do_not_disturb_hotkey" in config:
    config["control_panel_hotkey"] = config["do_not_disturb_hotkey"]
    print("Achtung! In deiner Config ist der Control Panel Hotkey noch unter 'do_not_disturb_hotkey' definiert! Für Kompatiblität zwischen alten Configs wird das automatisch korrigiert, aber bitte ändere den Namen des Schlüssels trotzdem.")

keyboard_module.add_hotkey(config["control_panel_hotkey"], toggle_überwachung)

bot.run(TOKEN)
