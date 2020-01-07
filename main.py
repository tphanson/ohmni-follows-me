import sys

import socket
import os
import os.path

import tensorflow as tf
from tests import wheel, cam
from ohmni import start as ohmni

tf.get_logger().setLevel('ERROR')

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
        if sys.argv[2] == 'cam':
            cam.start(server)

    elif sys.argv[1] == '--ohmni':
        if sys.argv[2] == 'start':
            ohmni.start()

    else:
        print("Error: Invalid option!")

print("-" * 20)
print("Shutting down...")
server.close()

os.remove("/dev/libcamera_stream")
print("Done")
