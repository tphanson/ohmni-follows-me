import time
import roslibpy
import cv2 as cv
import base64
import numpy as np
from datetime import datetime


def stringToRGB(base64_string):
    start = time.time()
    imgdata = base64.b64decode(base64_string)
    img = np.fromstring(imgdata, dtype=np.uint8)
    img = img.reshape((480, 640, 3))
    img = cv.cvtColor(img, cv.COLOR_RGB2BGR)
    end = time.time()
    print('Image estimated time {:.4f}'.format(end-start))
    return img


def callback(msg):
    print('=======================================')
    for key in ['encoding', 'height', 'header', 'step', 'width', 'is_bigendian']:
        print("***", key, msg[key])
    print("Image time", datetime.fromtimestamp(msg['header']['stamp']['secs']))
    print("Current time", datetime.now())
    img = stringToRGB(msg['data'])
    print(img.shape)


client = roslibpy.Ros(host='localhost', port=9090)
client.run()

listener = roslibpy.Topic(
    client,
    '/main_cam/image_raw',
    'sensor_msgs/Image',
    queue_size=1,
    queue_length=1
)
listener.subscribe(callback)

try:
    while True:
        pass
except KeyboardInterrupt:
    client.terminate()
