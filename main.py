import sys
import os
import socket
from tests import wheel
from ohmni import start as ohmni

###################################################################
if os.path.exists("/dev/libcamera_stream"):
    os.remove("/dev/libcamera_stream")

# Init botshell
botshell = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
botshell.connect("/app/bot_shell.sock")
botshell.sendall(b"wake_head\n")

server = "Abc"
# Init camera server
#rint("Oaening socket...")
#erver = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
#erver.bind("/dev/libcamera_stream")
#s.chown("/dev/libcamera_stream", 1047, 1047)

if __name__ == "__main__":

    if sys.argv[1] == "--test":
        if sys.argv[2] == 'wheel':
            wheel.start(botshell)

    elif sys.argv[1] == '--ohmni':
        if sys.argv[2] == 'debug':
            ohmni.start(server, botshell, debug=True)
        if sys.argv[2] == 'heteronomy':
            ohmni.start(server, botshell)
        if sys.argv[2] == 'autonomy':
            ohmni.start(server, botshell, autonomy=True)

    else:
        print("Error: Invalid option!")
