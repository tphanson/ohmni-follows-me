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


def fetch():

    state = SockState.SEARCHING
    imgdata = None
    framewidth = 0
    frameheight = 0
    frameformat = 0
    framesize = 0

    datagram = server.recv(65536)
    if not datagram:
        break

    if state == SockState.SEARCHING:
        if len(datagram) < 12 or len(datagram) > 64:
            continue
        if not datagram.startswith(b'OHMNICAM'):
            continue
        msgtype = unpack("I", datagram[8:12])
        if msgtype[0] == 1:
            params = unpack("IIII", datagram[12:28])

            state = SockState.FILLING
            imgdata = bytearray()

            framewidth = params[0]
            frameheight = params[1]
            frameformat = params[2]
            framesize = params[3]

    elif state == SockState.FILLING:
        imgdata.extend(datagram)
        if len(imgdata) < framesize:
            continue
        imgbytes = bytes(imgdata)
        newim = Image.frombytes(
            "L", (framewidth, frameheight), imgbytes, "raw", "L")
        rgbim = newim.convert("RGB")
        state = SockState.SEARCHING
        return rgbim


def terminate():
    print("-" * 20)
    print("Shutting down...")
    server.close()

    os.remove("/dev/libcamera_stream")
    print("Done")
