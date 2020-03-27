import time
import roslibpy
import numpy as np
import base64
import cv2 as cv
from utils import image


class ROSImage:
    def __init__(self):
        self.in_topic = '/main_cam/image_raw/compressed'
        self.out_topic = '/ofm/draw_image/compressed'
        self.in_data_type = 'sensor_msgs/CompressedImage'
        self.out_data_type = 'sensor_msgs/CompressedImage'
        self.header = None
        self.image = None
        self.msg = None

        self.client = roslibpy.Ros(host='192.168.0.100', port=9090)
        self.listener = roslibpy.Topic(
            self.client, self.in_topic, self.in_data_type,
            throttle_rate=70, queue_size=1)
        self.talker = roslibpy.Topic(
            self.client, self.out_topic, self.out_data_type)

    def __compressed_to_cv(self, _msg):
        buffer = base64.b64decode(_msg['data'])
        _img = np.fromstring(buffer, dtype=np.uint8)
        _img = cv.imdecode(_img, cv.IMREAD_COLOR)
        return _msg['header'], _img

    def __callback(self, _msg):
        self.msg = _msg
        self.header, self.image = self.__compressed_to_cv(_msg)

    def gen_compressed_img(self, _header, _img):
        _, buffer = cv.imencode('.jpeg', _img)
        _data = base64.b64encode(buffer)
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

    def push(self, _header, _img):
        msg = self.gen_compressed_img(_header, _img)
        self.talker.publish(roslibpy.Message(msg))


if __name__ == "__main__":
    ros = ROSImage()
    ros.start()

    try:
        while True:
            header, img = ros.get()
            if img is not None:
                # cv.imshow("debug", img)
                # cv.waitKey(10)
                ros.push(header, img)
            time.sleep(0.07)
    except KeyboardInterrupt:
        ros.stop()
