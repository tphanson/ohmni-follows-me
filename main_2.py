
from PIL import Image
import select
import v4l2capture

import time
import numpy as np
from utils.thread_camera import CamThread

from floor_detection.src.detector_2 import FloorDetection, ObstacleAvoidance
def detect_floor(fd, img):
    mask = fd.infer(img)
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
    print("time segment: ", time.time()-t_seg)
        

video.close()
