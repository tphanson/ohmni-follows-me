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
# Init camera server
print("Opening socket...")
server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
server.bind("/dev/libcamera_stream")
os.chown("/dev/libcamera_stream", 1047, 1047)

if __name__ == "__main__":
    if sys.argv[1] == "--test":
        if sys.argv[2] == 'wheel':
            wheel.start(botshell)

    elif sys.argv[1] == '--ohmni':
        if sys.argv[2] == 'start':
            ohmni.start(server, botshell, False)
        if sys.argv[2] == 'autonomy':
            ohmni.start(server, botshell, True)

    else:
        print("Error: Invalid option!")
