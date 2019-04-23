# Stalkbot

Cooler epischer Stalkbot mit dem deine Discord-Freunde dich stalken können.

## Installation

### Dependencies

Über Package-Manager:
* python3
* python3-pip
* python3-tk
* scrot
* ffmpeg
* portaudio (portaudio19-dev)
* xdotool


Über Pip (pip3 install PACKAGE):
* keyboard
* mouse
* pyautogui
* pillow
* opencv-python
* discord.py (async branch)
* numpy
* pyaudio
* gtts
* gtts-token
* psutil

### Aufsetzen des Bots
* Git Repository klonen -> `git clone https://github.com/Jerrynicki/Stalkbot`

#### Erstellen der config.json
```
{"token": "", 
"status": "",
"prefix": "",
"notifications": {"text": "", "duration":""},
"blacklist": [],
"webcamdelay": "",
"do_not_disturb_hotkey": "",
"folder": "",
"cooldown": ""}
```

Kopiere die leere config in eine neue Datei namens `config.json`, die einzelnen Optionen können wie folgt angepasst werden:
* token: Das Token deines Discord-Bots
* prefix: Der zu verwendende Prefix für Commands
* notifications:
* notifications.text: Der anzuzeigende Text bei der Notification, welche gesendet wird sobald ein Command ausgeführt wird. Gültige Flags sind:
> $AUTHOR: Der Autor der Nachricht in welcher der Command angefragt wurde

> $ACTION: Die Aktion, die ausgeführt wird

> $SERVER: Der Server, in dem der Command ausgeführt wird

> $CHANNEL: Der Channel, in dem der Command ausgeführt wird

* notifications.delay: Wie lange die Benachrichtigung angezeigt wird (in ms)

Eine beispielhafte Konfiguration des Benachrichtigungstexts wäre:
`"notifications": {"text": "$AUTHOR: $ACTION | $SERVER $CHANNEL", "duration":"8000"}`

* blacklist: User-IDs, welche keine Commands ausführen können, z.B.
`"blacklist": ["8", "69420", "2439422109419"]`

* webcamdelay: Wie lange gewartet wird, bis ein Foto mit der Webcam gemacht wird (in Sekunden)

* control\_panel\_hotkey (ehem. do\_not\_disturb\_hotkey): Der Hotkey zum Aufrufen des Control-Panels
`"control\_panel\_hotkey": "alt+end"` | Für zulässige Tastenkombinationen, siehe [hier](https://github.com/boppreh/keyboard#keyboard.all_modifiers)

* folder: Der zu verwendende Ordner für den Command `folder`, leer lassen, um den Command zu deaktivieren. Z.B: `"folder": "/home/niklas/Bilder"`

* cooldown: Wie lange die Ausführung vom Screenshot- und Webcam-Command verweigert wird nachdem er einmal ausgeführt wurde (in s)

#### Starten des Bots

* Nachdem alle Dependencies installiert sind und die config.json erstellt wurde, kann der Bot mit `sudo python3 main.py` gestartet werden.
