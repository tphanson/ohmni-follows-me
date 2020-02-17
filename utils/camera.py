from PIL import Image
from enum import Enum
from struct import unpack
import numpy as np
import cv2 as cv


class SockState(Enum):
    SEARCHING = 1
    FILLING = 2


def fetch(server):

    state = SockState.SEARCHING
    imgdata = None
    framewidth = 0
    frameheight = 0
    frameformat = 0
    framesize = 0

    while True:
        datagram = server.recv(65536)
        if not datagram:
            return None

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
            img_arr = np.fromstring(imgbytes, np.uint8)
            gimg = np.reshape(img_arr, (frameheight, framewidth))
            bgrimg = cv.cvtColor(gimg, cv.COLOR_GRAY2RGB)
            state = SockState.SEARCHING
            return bgrimg
