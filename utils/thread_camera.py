import numpy as np
import select
import v4l2capture
from PIL import Image

import threading
import time

class CamThread(threading.Thread):
    def __init__(self, camName, camID, size_x=480, size_y=640):
        threading.Thread.__init__(self)
        self.camID = camID
        self.camName = camName
        self.img = None
        self.size_x = size_x
        self.size_y = size_y

    def run(self):
        print("Starting " + self.camName)
        self.camPreview(self.camID)

    def camPreview(self, camID):
        self.cam = v4l2capture.Video_device(camID)
        size_x, size_y = self.cam.set_format(self.size_x, self.size_y)
        self.cam.create_buffers(1)
        self.cam.start()
        time.sleep(1)
        self.cam.queue_all_buffers()

        while True:
            select.select((self.cam,), (), ())
            img_data = self.cam.read_and_queue()
            img = Image.frombytes("RGB", (size_x, size_y), img_data)
            img = np.array(img)
            self.img = img

        self.cam.close()
