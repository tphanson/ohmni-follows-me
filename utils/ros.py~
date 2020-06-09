import roslibpy
import numpy as np
import base64
import cv2 as cv
import threading
import time


class ROSImage:
    def __init__(self):
        self.in_topic = '/main_cam/image_raw/compressed'
        self.out_topic = '/ofm/draw_image/compressed'
        self.in_data_type = 'sensor_msgs/CompressedImage'
        self.out_data_type = 'sensor_msgs/CompressedImage'
        self.header = None
        self.image = None
        self.seq = 0

        self.client = roslibpy.Ros(host='localhost', port=9090)
        self.listener = roslibpy.Topic(
            self.client, self.in_topic, self.in_data_type,
            throttle_rate=100, queue_size=1)
        self.talker = roslibpy.Topic(
            self.client, self.out_topic, self.out_data_type)

    def __compressed_to_cv(self, _msg):
        buffer = base64.b64decode(_msg['data'])
        _img = np.fromstring(buffer, dtype=np.uint8)
        _img = cv.imdecode(_img, cv.IMREAD_COLOR)
        return _msg['header'], _img

    def __callback(self, _msg):
        self.header, self.image = self.__compressed_to_cv(_msg)

    def __header(self):
        _time = time.time()
        self.seq += 1
        return {
            'stamp': {'secs': int(_time), 'nsecs': int(_time % 1*10**9)},
            'frame_id': 'ofm',
            'seq': self.seq
        }

    def gen_compressed_img(self, _img):
        _, buffer = cv.imencode('.jpeg', _img)
        _data = base64.b64encode(buffer)
        _header = self.__header()
        return {
            'header': _header,
            'data': _data.decode('utf-8'),
            'format': 'rgb8; jpeg compressed bgr8'
        }

    def isAlive(self):
        return self.client.is_connected

    def start(self):
        print("Start listening")
        self.client.run()
        self.listener.subscribe(self.__callback)

    def stop(self):
        self.talker.unadvertise()
        self.client.terminate()

    def get(self):
        return self.header, self.image

    def push(self, _img):
        msg = self.gen_compressed_img(_img)
        self.talker.publish(roslibpy.Message(msg))

    def apush(self, _img):
        t = threading.Thread(target=self.push, args=(_img,), daemon=True)
        t.start()
