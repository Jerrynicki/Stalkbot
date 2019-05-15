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
from PIL import Image, ImageFilter
import urllib.request
import urllib.parse
import json
import random
import tkinter as tk
import wave
import audioop
import pyautogui
import sys
import multiprocessing
import keyboard as keyboard_module
import mouse

import tts_download
import sum_process_resources

def alert(message):
    root1 = tk.Tk()
    root1.title("Stalkbot: Warnung")
    tk.Label(root1, text=message, font=("Helvetica", 15)).pack()
    tk.Button(root1, text="Okay", font=("Helvetica", 15), command=root1.quit).pack()
    root1.mainloop()
    root1.destroy()

if sys.version_info[1] < 6:
    import collections
    dict = collections.OrderedDict
    print("Python interpreter < 3.6 festgestellt, ersetze `dict` mit `collections.OrderedDict`.")

PLATFORM = sys.platform
if PLATFORM.lower().startswith("win"):
    PLATFORM = "windows"

if PLATFORM == "windows":
    import winsound
    from PIL import ImageGrab
    from win10toast import ToastNotifier
    FFMPEG_EXECUTABLE = "ffmpeg.exe"
else:
    import pyaudio
    FFMPEG_EXECUTABLE = "ffmpeg"

if os.path.isfile("ffmpeg_override.txt"):
    override_path = open("ffmpeg_override.txt", "r").read()
    FFMPEG_EXECUTABLE = override_path
    print("FFmpeg override: " + override_path)

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
hourglass_emoji = "\U000023F3"

def format_notification(message, action):
    notify_config = config["notifications"]["text"]
    notify_text = notify_config.replace("$AUTHOR", message.author.name).replace("$SERVER", message.server.name).replace("$CHANNEL", "#" + message.channel.name).replace("$ACTION", action)
    return notify_text

def notification(action, ctx):
    global command_log

    notify_text = format_notification(ctx.message, action)
    command_log.append([time.time(), ctx.message, action])
    if PLATFORM == "windows":
        ToastNotifier().show_toast("Stalkbot", notify_text, icon_path=None, duration=int(config["notifications"]["duration"])/1000, threaded=True)
    else:
        subprocess.call(["notify-send", "-t", config["notifications"]["duration"], "Stalkbot", notify_text])

def _play_file_win():
    try:
        file = open("winsound_file.tmp", "r").read()
        winsound.PlaySound(file, winsound.SND_FILENAME)
    except Exception as exc:
        with open("winsound_error.tmp", "w") as tmp:
            tmp.write(str(exc))

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

    timed_out = False

    if PLATFORM == "windows":
        with open("winsound_file.tmp", "w") as tmp:
            tmp.write(file)
        proc = multiprocessing.Process(target=_play_file_win)
        proc.daemon = True
        proc.start()

        proc.join(10)
        if proc.is_alive():
            proc.terminate()
            timed_out = True
    else:
        p = pyaudio.PyAudio()  
        stream = p.open(format = p.get_format_from_width(f.getsampwidth()), channels = f.getnchannels(), rate = f.getframerate(), output = True)
        data = f.readframes(chunk)

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

if __name__ == "__main__":
    config = json.load(open("config.json", "r"))

    blacklist = config["blacklist"]
    TOKEN = config["token"]
    config["cooldown"] = int(config["cooldown"])

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
    command_log = []

    if not os.path.isdir("cache"):
        os.mkdir("cache")

    async def clear_old_commands():
        global command_log

        to_remove = []
        tm = time.time()
        deleted = 0
        for x in range(len(command_log)):
            x = x - deleted
            if command_log[x][0] + 600 < tm:
                del command_log[x]
                deleted += 1

    @bot.event
    async def on_ready():
        print("Logged in as " + bot.user.name + "#" + bot.user.discriminator)
        await asyncio.sleep(5)
        while True:
            await bot.change_presence(status=discord.Status.online, game=discord.Game(name=config["status"]))
            await clear_old_commands()
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

            proc = multiprocessing.Process(target=tts_download.download, args=(ctx.message.author.name + "sagt: " + message, FFMPEG_EXECUTABLE))
            proc.start()
            proc.join(10)
            if proc.is_alive():
                proc.terminate()
                raise TimeoutError
            await bot.remove_reaction(ctx.message, repeat_emoji, ctx.message.server.me)
            await bot.add_reaction(ctx.message, play_emoji)

            notification("TTS: " + message, ctx)

            try:
                sound_playing = True
                play_file("cache/tmp.wav", timeout=20)
                await bot.remove_reaction(ctx.message, play_emoji, ctx.message.server.me)
                await bot.add_reaction(ctx.message, white_check_mark_emoji)
            except:
                await bot.remove_reaction(ctx.message, play_emoji, ctx.message.server.me)
                await bot.add_reaction(ctx.message, stop_sign_emoji)
        except Exception as exc:
            await bot.remove_reaction(ctx.message, play_emoji, ctx.message.server.me)
            await bot.add_reaction(ctx.message, negative_squared_cross_mark_emoji)
            await bot.say("`" + str(exc) + "`")

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

        if image_lock or not ueberwachung:
            await bot.add_reaction(ctx.message, negative_squared_cross_mark_emoji)
            return

        if time.time() < image_countdown:
            await bot.add_reaction(ctx.message, hourglass_emoji)
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
            image_countdown = time.time() + config["cooldown"]


    screenshot_lock = False
    screenshot_countdown = 0


    @bot.command(pass_context=True, aliases=["scr", "sc", "ss"])
    async def screenshot(ctx):
        global screenshot_lock
        global screenshot_countdown

        if not ueberwachung["screenshot"]:
            await bot.add_reaction(ctx.message, no_bell_emoji)
            return
        
        if screenshot_lock:
            await bot.add_reaction(ctx.message, negative_squared_cross_mark_emoji)
            return

        if time.time() < screenshot_countdown:
            await bot.add_reaction(ctx.message, hourglass_emoji)
            return

        if ctx.message.author.id in blacklist:
            await bot.say(ctx.message.author.mention + " hurensohn bist geblacklistet weil du hurensohn bist\nfick dich")
            return

        try:
            screenshot_lock = True

            play_file("warning_sound.wav", timeout="auto")
            notification("Screenshot", ctx)

            await bot.add_reaction(ctx.message, repeat_emoji)

            if PLATFORM == "windows":
                screenshot = ImageGrab.grab()
            else:
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
            screenshot_countdown = time.time() + config["cooldown"]


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

            subprocess.call([FFMPEG_EXECUTABLE, "-y", "-i", "cache/tmp." + ctx.message.attachments[0]
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

        if mouse_keyboard_ctrl == "keyboard":
            mouse.move(x, y, duration=0.5)
        else:
            pyautogui.moveTo(x, y, duration=0.5)

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

        if mouse_keyboard_ctrl == "keyboard":
            keyboard_module.write(text, delay=0.05, exact=True)
        else:
            pyautogui.typewrite(text, interval=0.05)

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
                      no_entry_emoji + " Eine TTS-Nachricht wird gerade schon abgespielt\n" +
                      hourglass_emoji + " Cooldown aktiv")


    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        await bot.process_commands(message)

    def edit_config():
        global config

        root = tk.Tk()
        root.title("Stalkbot Config Editor")

        if sys.version_info[1] < 6: # Der Code ist hässlich weil er nur temporär ist, bugfix bald tm
            alert("Warnung!\nDein Python Interpreter ist < Version 3.6.\nEin alternativer Config-Editor wird fürs Erste verwendet. Ein Fix kommt bald.")
            def return_press(*args):
                root.quit()
            editor = tk.Text(root, font=("Helvetica", 13))
            editor.pack()
            editor.insert(tk.END, json.dumps(config, indent=2))
            done = tk.Button(root, text="Fertig", font=("Helvetica", 13), command=root.quit)
            done.pack()
            root.bind("<Escape>", return_press)
            root.mainloop()
            config = json.loads(editor.get("1.0", tk.END))
            json.dump(config, open("config.json", "w"), indent=2)
            root.destroy()
            return

        def done():
            global config
            reconstructed_config = {}
            for key, i in zip(tmp_config, range(len(tmp_config))):
                tmp_config[key] = entries[i].get()

                if type(tmp_config[key]) == type(config[key]):
                    config[key] = tmp_config[key]
                else:
                    print(key)
                    print(tmp_config)
                    print(tmp_config[key])
                    config[key] = json.loads(tmp_config[key])
            
            root.destroy()

        frame1 = tk.Frame(root)
        frame1.grid(row=0, column=0)

        frame2 = tk.Frame(root)
        frame2.grid(row=0, column=1)

        frame3 = tk.Frame(root)
        frame3.grid(row=1, column=0)

        tmp_config = config.copy()

        labels = []
        for key in config:
            if type(tmp_config[key]) != str:
                tmp_config[key] = json.dumps(tmp_config[key])
            labels.append(tk.Label(frame1, text=key, font=("Helvetica", 13)))
            labels[-1].pack()

        entries = []
        for key in config:
            entries.append(tk.Entry(frame2, font=("Helvetica", 13), width=50))
            entries[-1].pack()
            entries[-1].insert(0, tmp_config[key])

        info_lbl = tk.Label(frame3, text="Token, Prefix und der Control Panel Hotkey benötigen einen Neustart.", font=("Helvetica", 14))
        info_lbl.pack()

        done_bt = tk.Button(frame3, text="Fertig", command=done, font=("Helvetica", 14))
        done_bt.pack()

        while True:
            try:
                root.update()
                time.sleep(1/30)
            except:
                break

        json.dump(config, open("config.json", "w"), indent=2)

    def show_log():
        def close():
            root.quit()

        def update():
            box.delete(0, tk.END)
            cmd_log = command_log.copy()
            tm = time.time()
            for x in cmd_log:
                diff = tm - x[0]
                elapsed = "vor " + str(int(diff // 60)) + "m " + str(int(diff % 60)) + "s"
            
                box.insert(tk.END, elapsed + " | " + format_notification(x[1], x[2]))

            root.after(1000, update)

        root = tk.Tk()
        root.title("Stalkbot: Command-Log")

        box = tk.Listbox(root, height=10, width=90, font=("Helvetica", 13))
        box.pack()

        done = tk.Button(root, text="Fertig", command=close, font=("Helvetica", 15))
        done.pack()

        root.after(200, update)
        root.mainloop()
        root.destroy()

    def toggle_überwachung():
        global ueberwachung
        root = tk.Tk()
        root.title("Stalkbot Überwachung Control-Panel")

        def toggle(key):
            if ueberwachung[key]:
                ueberwachung[key] = False
            else:
                ueberwachung[key] = True

            if key == "global":
                if ueberwachung["global"]:
                    for key in ueberwachung:
                        ueberwachung[key] = True
                else:
                    for key in ueberwachung:
                        ueberwachung[key] = False

        def stats_update():
            """
            ping_start = time.time()
            ws = bot.ws
            ping = await ws.ping()
            await ping
            ping_end = time.time()
            ping = int((ping_start-ping_end)*1000)
            """
            ping = "N/A"

            ping_lbl.config(text="Ping: " + str(ping) + "ms")

            if bot.ws and bot.user:
                if bot.ws.open:
                    conn_lbl.config(text="Online", fg="green")
                else:
                    conn_lbl.config(text="Offline", fg="red")
            else:
                conn_lbl.config(text="Offline", fg="red")

            root.after(500, stats_update)

        def buttons_update():
            for key, i in zip(ueberwachung, range(len(ueberwachung))):
                buttons[i].config(text=key.capitalize() + ": " + str(ueberwachung[key]))
            
            root.after(100, buttons_update)

        conn_lbl = tk.Label(root, font=("Helvetica", 17))
        ping_lbl = tk.Label(root, font=("Helvetica", 17))
        conn_lbl.pack()
        ping_lbl.pack()

        buttons = []
        for key in ueberwachung:
            buttons.append(tk.Button(root, text=key.capitalize() + ": " + str(ueberwachung[key]), command=lambda key=key: toggle(key), font=("Helvetica", 16)))
            buttons[-1].pack()

        config_bt = tk.Button(root, text="Config bearbeiten", command=edit_config, font=("Helvetica", 14))
        config_bt.pack()

        log_bt = tk.Button(root, text="Command-Log öffnen", command=show_log, font=("Helvetica", 14))
        log_bt.pack()

        done_bt = tk.Button(root, text="Fertig", command=root.quit, font=("Helvetica", 14))
        done_bt.pack()

        root.after(200, stats_update)
        root.after(200, buttons_update)
        root.mainloop()
        root.destroy()
        json.dump(ueberwachung, open("ueberwachung_retain.json", "w"))

    def auto_restart_control_panel():
        while True:
            toggle_überwachung()

    if not "control_panel_hotkey" in config and "do_not_disturb_hotkey" in config:
        config["control_panel_hotkey"] = config["do_not_disturb_hotkey"]
        print("Achtung! In deiner Config ist der Control Panel Hotkey noch unter 'do_not_disturb_hotkey' definiert! Für Kompatiblität zwischen alten Configs wird das automatisch korrigiert, aber bitte ändere den Namen des Schlüssels trotzdem.")

    try:
        keyboard_module.add_hotkey(config["control_panel_hotkey"], toggle_überwachung)
        mouse_keyboard_ctrl = "keyboard"
    except ImportError:
        alert("Konnte Hotkey nicht per `keyboard` festlegen (Linux: Bist du kein root?), wechsle zu pyautogui...\n\nACHTUNG: Mit dieser Konfiguration kann das Control Panel nicht per Hotkey aufgerufen werden.\nEs wurde automatisch geöffnet und wird wieder neu gestartet, sobald es geschlossen wird.")
        threading.Thread(target=auto_restart_control_panel).start()
        mouse_keyboard_ctrl = "pyautogui"

    bot.run(TOKEN)
    print("bot.run() ended, restarting in 10 seconds...")
    time.sleep(10)
    os.execvp(sys.executable, [sys.executable, sys.argv[0]])
