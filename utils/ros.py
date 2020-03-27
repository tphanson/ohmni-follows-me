import time
import roslibpy
import numpy as np
import base64
import cv2 as cv
from datetime import datetime


class ROSImage:
    def __init__(self):
        self.in_topic = '/main_cam/image_raw/compressed'
        self.out_topic = '/ofm/image'
        self.in_data_type = 'sensor_msgs/CompressedImage'
        self.out_data_type = 'sensor_msgs/String'
        self.image = None
        self.buffer = None

        self.client = roslibpy.Ros(host='localhost', port=9090)
        self.listener = roslibpy.Topic(
            self.client, self.in_topic, self.in_data_type,
            throttle_rate=70, queue_size=1)
        self.talker = roslibpy.Topic(
            self.client, self.out_topic, self.out_data_type,
            throttle_rate=70, queue_size=1)

    def __compressed_to_cv(self, msg):
        data = base64.b64decode(msg['data'])
        img = np.fromstring(data, dtype=np.uint8)
        img = cv.imdecode(img, cv.IMREAD_COLOR)
        return img

    def isAlive(self):
        return self.client.is_connected

    def __callback(self, msg):
        stamp = msg['header']['stamp']
        img_time = float(str(stamp['secs'])+'.'+str(stamp['nsecs']))
        self.buffer = "Image time" + \
            str(datetime.fromtimestamp(img_time)) + \
            "Current time" + str(datetime.now())
        self.image = self.__compressed_to_cv(msg)

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
