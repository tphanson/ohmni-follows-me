import time
import roslibpy
import cv2 as cv
import base64
import numpy as np
from datetime import datetime


def compressed_to_cv(msg):
    start = time.time()
    data = msg['data']
    # data = base64.b64decode(msg['data'])
    img = np.fromstring(data, dtype=np.uint8)
    print(img.shape)
    # img = img.reshape((480, 640, 3))
    # img = cv.cvtColor(img, cv.COLOR_RGB2BGR)
    end = time.time()
    print('Image estimated time {:.4f}'.format(end-start))
    return img


def callback(msg):
    print('=======================================')
    for key in ['header', 'data', 'format']:
        print("***", key, msg[key])
    start = time.time()
    stamp = msg['header']['stamp']
    img_time = float(str(stamp['secs'])+'.'+str(stamp['nsecs']))
    print("Image time", datetime.fromtimestamp(img_time))
    print("Current time", datetime.now())
    img = compressed_to_cv(msg)
    # print(img.shape)
    end = time.time()
    print('Callback estimated time {:.4f}'.format(end-start))


client = roslibpy.Ros(host='localhost', port=9090)
client.run()

listener = roslibpy.Topic(
    client,
    '/main_cam/image_raw/compressed',
    'sensor_msgs/CompressedImage',
    throttle_rate=70,
    queue_size=1
)
listener.subscribe(callback)

try:
    while True:
        pass
except KeyboardInterrupt:
    client.terminate()
