import platform
import subprocess
import signal
from PIL import Image, ImageDraw

import socket
import os
import os.path
import time
from enum import Enum
from struct import *

# Open connection to bot shell
botshell = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
botshell.connect("/app/bot_shell.sock")
#botshell.sendall(b"say hello\n")
botshell.sendall(b"wake_head\n")

if os.path.exists("/dev/libcamera_stream"):
    os.remove("/dev/libcamera_stream")\

print("Opening socket...")
server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
server.bind("/dev/libcamera_stream")
os.chown("/dev/libcamera_stream", 1047, 1047)


class SockState(Enum):
    SEARCHING = 1
    FILLING = 2


def keyboardInterruptHandler(signal, frame):
    print("Stopping...")
    botshell.sendall("manual_move 0 0\n".encode())
    exit(0)


signal.signal(signal.SIGINT, keyboardInterruptHandler)


def start():

    print("Listening...")
    server.settimeout(0.5)

    botshell.sendall("manual_move -100 100\n".encode())
    time.sleep(2)
    botshell.sendall("manual_move 100 -100\n".encode())
    time.sleep(2)

    print("-" * 20)
    print("Shutting down...")
    server.close()

    os.remove("/dev/libcamera_stream")
    print("Done")
