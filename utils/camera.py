import socket
import os
from enum import Enum
from struct import unpack
import numpy as np
import cv2 as cv


class SockState(Enum):
    SEARCHING = 1
    FILLING = 2


class Camera:
    def __init__(self):
        if os.path.exists("/dev/libcamera_stream"):
            os.remove("/dev/libcamera_stream")
        self.server = None

    def isAlive(self):
        return False if self.server is None else True

    def start_server(self):
        if self.server is not None:
            return False
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.server.settimeout(0.2)
        self.server.bind("/dev/libcamera_stream")
        os.chown("/dev/libcamera_stream", 1047, 1047)
        return True

    def stop_server(self):
        if self.server is None:
            return True
        self.server.close()
        os.remove("/dev/libcamera_stream")
        self.server = None
        return True

    def fetch(self):
        if self.server is None:
            return None

        state = SockState.SEARCHING
        imgdata = None
        framewidth = 0
        frameheight = 0
        framesize = 0

        while True:
            try:
                datagram = self.server.recv(65536)
            except:
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
