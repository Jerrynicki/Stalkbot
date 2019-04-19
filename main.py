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
import keyboard
import sum_process_resources
import urllib.request
import urllib.parse
import json
import random

logging.basicConfig(level=logging.INFO)

sound_playing = False

repeat_emoji = "\U0001F501"
play_emoji = "\U000025B6"
white_check_mark_emoji = "\U00002611"
stop_sign_emoji = "\U0001F6D1"
negative_squared_cross_mark_emoji = "\U0000274E"
no_entry_emoji = "\U000026D4"

config = json.load(open("config.json", "r"))

blacklist = config["blacklist"]
TOKEN = config["token"]

bot = commands.Bot(command_prefix=config["prefix"], description="jejei")

if not os.path.isdir("cache"):
    os.mkdir("cache")

def notification(action, ctx):
    notify_config = config["notifications"]["text"]
    subprocess.call(["notify-send", "-t", config["notifications"]["duration"], notify_config.replace("$AUTHOR", ctx.message.author.name).replace("$SERVER", ctx.message.server.name).replace("$CHANNEL", "#" + ctx.message.channel.name).replace("$ACTION", action)])


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

        proc = subprocess.Popen(["python3", "tts_play.py"])
        try:
            sound_playing = True
            proc.wait(timeout=20)
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

ueberwachung = True

image_lock = False
image_countdown = 0


@bot.command(pass_context=True, aliases=["cam", "wc"])
async def webcam(ctx):
    global image_lock
    global image_countdown

    if image_lock or image_countdown > time.time() or not ueberwachung:
        await bot.add_reaction(ctx.message, negative_squared_cross_mark_emoji)
        return

    if ctx.message.author.id in blacklist:
        await bot.say(ctx.message.author.mention + " hurensohn bist geblacklistet weil du hurensohn bist\nfick dich")
        return

    await bot.add_reaction(ctx.message, repeat_emoji)

    image_lock = True

    try:
        proc = subprocess.Popen(["python3", "warning_sound.py"])
        proc.wait(timeout=2)
        notification("Webcam", ctx)

        cam = cv2.VideoCapture(0) 
        await asyncio.sleep(int(config["webcamdelay"]))
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
    if screenshot_lock or screenshot_countdown > time.time() or not ueberwachung:
        await bot.add_reaction(ctx.message, negative_squared_cross_mark_emoji)
        return

    if ctx.message.author.id in blacklist:
        await bot.say(ctx.message.author.mention + " hurensohn bist geblacklistet weil du hurensohn bist\nfick dich")
        return

    try:
        screenshot_lock = True

        proc = subprocess.Popen(["python3", "warning_sound.py"])
        proc.wait(timeout=2)
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

    if ctx.message.author.id in blacklist:
        await bot.say(ctx.message.author.mention + " hurensohn bist geblacklistet weil du hurensohn bist\nfick dich")
        return

    if not arg or arg not in ("cpu", "ram", "focused"):
        await bot.say("Bitte gebe als Argument entweder `cpu`, `ram` oder `focused` an.")
        return

    if not ueberwachung:
        await bot.add_reaction(ctx.message, negative_squared_cross_mark_emoji)
        return

    proc = subprocess.Popen(["python3", "warning_sound.py"])
    proc.wait(timeout=2)
    
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
            info = info.split("\n")
            del info[1]
            info.insert(0, "Aktives Fenster: ")
            
            info[2] = info[2].split(" ")
            print(info[2])
            tup = info[2][3].split(",")
            tup = (int(tup[0]), int(tup[1]))
            if tup[0] > 1920:
                info[2][-1] = "1)"
            else:
                info[2][-1] = "0)"

            info[2] = " ".join(info[2])
            
            info = "\n".join(info)

        await bot.say(info)



@bot.command(pass_context=True)
async def miku(ctx):
    """Miku-Command für Sukeldukel uwu"""


@bot.command(pass_context=True)
async def play(ctx, *url):
    """Spielt eine beliebige (mit FFmpeg kompatible) Audiodatei ab"""

    global sound_playing

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

        proc = subprocess.Popen(["python3", "warning_sound.py"])
        proc.wait(timeout=2)
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
        proc = subprocess.Popen(["python3", "file_play.py"])
        try:
            sound_playing = True
            proc.wait(timeout=20)
            await bot.remove_reaction(ctx.message, play_emoji, ctx.message.server.me)
            await bot.add_reaction(ctx.message, white_check_mark_emoji)
        except:
            await bot.remove_reaction(ctx.message, play_emoji, ctx.message.server.me)
            await bot.add_reaction(ctx.message, stop_sign_emoji)
    except Exception as exc:
        await bot.remove_reaction(ctx.message, play_emoji, ctx.message.server.me)
        await bot.add_reaction(ctx.message, negative_squared_cross_mark_emoji)
        print(exc)

    proc.terminate()
    sound_playing = False
    os.unlink("cache/tmp." + ctx.message.attachments[0]["url"].split(".")[-1])


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

    if ueberwachung:
        ueberwachung = False
        subprocess.call(["notify-send", "TTS-Bot: Überwachungsmodule deaktiviert", "-t", "3000"])

    else:
        ueberwachung = True
        subprocess.call(["notify-send", "TTS-Bot: Überwachungsmodule aktiviert", "-t", "3000"])


keyboard.add_hotkey(config["do_not_disturb_hotkey"], toggle_überwachung)

bot.run(TOKEN)
