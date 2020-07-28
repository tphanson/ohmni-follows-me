import roslibpy
import numpy as np
import base64
import cv2 as cv
import threading
import time


class Listener:
    def __init__(self, client, topic, data_type='sensor_msgs/CompressedImage'):
        self.client = client
        self.topic = topic
        self.data_type = data_type

        self.listener = roslibpy.Topic(self.client, self.topic, self.data_type,
                                       throttle_rate=100, queue_size=1)
        self.listener.subscribe(self.__callback)
        self.header = None
        self.image = None

    def __compressed_to_cv(self, msg):
        buffer = base64.b64decode(msg['data'])
        img = np.fromstring(buffer, dtype=np.uint8)
        img = cv.imdecode(img, cv.IMREAD_COLOR)
        return msg['header'], img

    def __callback(self, msg):
        self.header, self.image = self.__compressed_to_cv(msg)

    def get(self):
        return self.header, self.image

    def stop(self):
        pass


class Talker:
    def __init__(self, client, topic, data_type='sensor_msgs/CompressedImage'):
        self.client = client
        self.topic = topic
        self.data_type = data_type

        self.talker = roslibpy.Topic(self.client, self.topic, self.data_type)
        self.seq = 0

    def __header(self):
        _time = time.time()
        self.seq += 1
        return {
            'stamp': {'secs': int(_time), 'nsecs': int(_time % 1*10**9)},
            'frame_id': 'ofm',
            'seq': self.seq
        }

    def _compress_img(self, _img):
        _, buffer = cv.imencode('.jpeg', _img)
        _data = base64.b64encode(buffer)
        _header = self.__header()
        return {
            'header': _header,
            'data': _data.decode('utf-8'),
            'format': 'rgb8; jpeg compressed bgr8'
        }

    def _sync_push(self, img):
        msg = self._compress_img(img)
        self.talker.publish(roslibpy.Message(msg))

    def _async_push(self, img):
        t = threading.Thread(target=self._sync_push, args=(img,), daemon=True)
        t.start()

    def push(self, img):
        self._async_push(img)

    def stop(self):
        self.talker.unadvertise()


class ROSImage:
    def __init__(self, host='localhost', port=9090):
        self.host = host
        self.port = port
        self.client = roslibpy.Ros(host=self.host, port=self.port)
        self.client.run()

    def isAlive(self):
        return self.client.is_connected

    def gen_talker(self, topic):
        """ For topic examples: '/ofm/draw_image/compressed' """
        return Talker(self.client, topic)

    def gen_listener(self, topic):
        """ For topic examples: '/main_cam/image_raw/compressed' """
        return Listener(self.client, topic)

    def stop(self):
        self.client.terminate()
