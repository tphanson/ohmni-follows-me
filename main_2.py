
from PIL import Image
import select
import v4l2capture

import time
import numpy as np
from utils.thread_camera import CamThread

import base64
import zmq
import cv2
#server to stream to the laptop to visualize
context = zmq.Context()
footage_socket = context.socket(zmq.PUB)
ip = "tcp://192.168.123.42:5555"
footage_socket.connect(ip)

from floor_detection.src.detector_2 import FloorDetection, ObstacleAvoidance
def detect_floor(fd, img):
    _, mask = fd.predict(img)
    return mask

fd = FloorDetection()

# Open the video device.
video = v4l2capture.Video_device("/dev/video1")

size_x, size_y = video.set_format(640, 480)


video.create_buffers(1)

video.start()

video.queue_all_buffers()

while True:
    # Wait for the device to fill the buffer.
    select.select((video,), (), ())

    img_data = video.read_and_queue()

    img = Image.frombytes("RGB", (size_x, size_y), img_data)
    img = np.array(img)

    # Detect floor
    t_seg = time.time()
    mask = detect_floor(fd, img)
    mask = np.array(mask)
    mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    mask[np.where(mask == 0)] = 0
    mask[np.where(mask == 1)] = 255
    #stream to the laptop
    encoded, buffer = cv2.imencode('.jpg', mask)
    jpg_as_text = base64.b64encode(buffer)
    footage_socket.send(jpg_as_text)

    print("time segment: ", time.time()-t_seg)
        

video.close()
