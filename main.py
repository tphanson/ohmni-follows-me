import sys

import tensorflow as tf
from tests import camera, wheel, cam
from ohmni import start as ohmni

tf.get_logger().setLevel('ERROR')

if __name__ == "__main__":
    if sys.argv[1] == "--test":
        if sys.argv[2] == 'camera':
            camera.start()
        if sys.argv[2] == 'wheel':
            wheel.start()
        if sys.argv[2] == 'cam':
            cam.start()

    elif sys.argv[1] == '--ohmni':
        if sys.argv[2] == 'start':
            ohmni.start()

    else:
        print("Error: Invalid option!")
