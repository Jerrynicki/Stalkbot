# Stalkbot

Cooler epischer Stalkbot mit dem deine Discord-Freunde dich stalken können.

## Installation

### Dependencies

Über Package-Manager:
* python3
* python3-pip
* scrot
* ffmpeg
* portaudio
* xdotool


Über Pip (pip3 install PACKAGE):
* keyboard
* pillow
* opencv-python
* discord.py
* numpy
* pyaudio
* gtts
* gtts-token

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
"do_not_disturb_hotkey": ""}
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

* do_not_disturb_hotkey: Der Hotkey, mit welchem alle "Spionagefunktionen" des Bots deaktiviert werden, z.B.
`"do_not_disturb_hotkey": "alt+end"` | Für zulässige Tastenkombinationen, siehe [hier](https://github.com/boppreh/keyboard#keyboard.all_modifiers)

#### Starten des Bots

* Nachdem alle Dependencies installiert sind und die config.json erstellt wurde, kann der Bot mit `sudo python3 main.py` gestartet werden.
