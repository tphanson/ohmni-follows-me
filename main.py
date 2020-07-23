import sys
import os
import socket
from tests import wheel
from ohmni import start as ohmni


if os.path.exists("/dev/libcamera_stream"):
    os.remove("/dev/libcamera_stream")

# Init botshell
botshell = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
botshell.connect("/app/bot_shell.sock")
botshell.sendall(b"wake_head\n")

if __name__ == "__main__":
    if sys.argv[1] == "--test":
        if sys.argv[2] == 'wheel':
            wheel.start(botshell)

    elif sys.argv[1] == '--ohmni':
        if sys.argv[2] == 'debug':
            ohmni.start(botshell, debug=True)
        if sys.argv[2] == 'heteronomy':
            ohmni.start(botshell)
        if sys.argv[2] == 'autonomy':
            ohmni.start(botshell, autonomy=True)

    else:
        print("Error: Invalid option!")
