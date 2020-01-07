from PIL import Image
import socket
import os
import os.path
from enum import Enum
from struct import *


if os.path.exists("/dev/libcamera_stream"):
    os.remove("/dev/libcamera_stream")

print("Opening socket...")
server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
server.bind("/dev/libcamera_stream")
os.chown("/dev/libcamera_stream", 1047, 1047)


class SockState(Enum):
    SEARCHING = 1
    FILLING = 2


def start():

    state = SockState.SEARCHING
    imgdata = None
    framewidth = 0
    frameheight = 0
    frameformat = 0
    framesize = 0

    print("Listening...")
    while True:

        datagram = server.recv(65536)
        if not datagram:
            break

        # Handle based on state machine
        if state == SockState.SEARCHING:

            # Check for non-control packets
            if len(datagram) < 12 or len(datagram) > 64:
                continue

            # Check for magic
            if not datagram.startswith(b'OHMNICAM'):
                continue

            # Unpack the bytes here now for the message type
            msgtype = unpack("I", datagram[8:12])
            if msgtype[0] == 1:
                params = unpack("IIII", datagram[12:28])

                state = SockState.FILLING
                imgdata = bytearray()

                framewidth = params[0]
                frameheight = params[1]
                frameformat = params[2]
                framesize = params[3]

        # Filling image buffer now
        elif state == SockState.FILLING:

            # Append to buffer here
            imgdata.extend(datagram)

            # Check size
            if len(imgdata) < framesize:
                continue

            # Resize and submit
            imgbytes = bytes(imgdata)
            newim = Image.frombytes(
                "L", (framewidth, frameheight), imgbytes, "raw", "L")
            rgbim = newim.convert("RGB")

            print(rgbim)

            # Go back to initial state
            state = SockState.SEARCHING

    print("-" * 20)
    print("Shutting down...")
    server.close()

    os.remove("/dev/libcamera_stream")
    print("Done")
