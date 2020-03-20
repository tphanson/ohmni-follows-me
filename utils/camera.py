import socket
import os
from enum import Enum
from struct import unpack
import numpy as np
import cv2 as cv
import rospy
from sensor_msgs.msg import Image


class SockState(Enum):
    SEARCHING = 1
    FILLING = 2


class Camera:
    def __init__(self):
        self.itopic = '/main_cam/image_raw'
        self.otopic = '/debug/image'
        self.image = None
        self.publisher = None

    def isAlive(self):
        return False if self.image is None else True

    def callback(self, data):
        print("Transfering data")
        self.image = data
        self.publisher.publish(data)

    def start_server(self):
        print("Start listening")
        rospy.Subscriber(self.itopic, Image, self.callback)
        self.publisher = rospy.Publisher(self.otopic, Image, queue_size=1)

    def stop_server(self):
        pass

    def fetch(self):
        return self.image
