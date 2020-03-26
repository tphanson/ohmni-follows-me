import time
import roslibpy
import numpy as np
import base64
import cv2 as cv


class ROSImage:
    def __init__(self):
        self.in_topic = '/main_cam/image_raw'
        self.out_topic = '/ofm/image'
        self.data_type = 'sensor_msgs/Image'
        self.image = None

        self.client = roslibpy.Ros(host='localhost', port=9090)
        self.talker = roslibpy.Topic(
            self.client, self.out_topic, self.data_type, queue_size=10)
        self.listener = roslibpy.Topic(
            self.client, self.in_topic, self.data_type)

    def convert_base64_to_image(self, base64_string):
        start = time.time()
        imgdata = base64.b64decode(base64_string)
        img = np.fromstring(imgdata, dtype=np.uint8)
        img = img.reshape((480, 640, 3))
        img = cv.cvtColor(img, cv.COLOR_RGB2BGR)
        end = time.time()
        print('Converting image estimated time {:.4f}'.format(end-start))
        return img

    def isAlive(self):
        return self.client.is_connected

    def __callback(self, msg):
        self.image = self.convert_base64_to_image(msg['data'])

    def start(self):
        print("Start listening")
        self.client.run()
        self.listener.subscribe(self.__callback)

    def stop(self):
        self.client.terminate()

    def get(self):
        return self.image

    def push(self):
        pass
