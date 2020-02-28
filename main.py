import sys

import socket
from tests import wheel, cam
from ohmni import start as ohmni


# Init botshell
botshell = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
botshell.connect("/app/bot_shell.sock")
botshell.sendall(b"wake_head\n")

if __name__ == "__main__":
    if sys.argv[1] == "--test":
        if sys.argv[2] == 'wheel':
            wheel.start(botshell)

    elif sys.argv[1] == '--ohmni':
        if sys.argv[2] == 'start':
            ohmni.start(botshell)

    else:
        print("Error: Invalid option!")
