from PIL import Image
from enum import Enum
from struct import *


class SockState(Enum):
    SEARCHING = 1
    FILLING = 2


def start(server):

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

                print(framewidth, frameheight, frameformat, framesize)

        # Filling image buffer now
        if state == SockState.FILLING:

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
