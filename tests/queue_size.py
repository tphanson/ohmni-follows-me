#!/usr/bin/env python

import rospy
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from datetime import datetime
import time


if __name__ == '__main__':
    rospy.init_node('ohmnicam', anonymous=True)

    bridge = CvBridge()

    def callback(data):
        img_time = data.header.stamp.secs
        rospy.loginfo('Image time %s' % str(datetime.fromtimestamp(img_time)))
        rospy.loginfo('Current time %s' % str(datetime.now()))
        time.sleep(1)

    rospy.Subscriber('/main_cam/image_raw', Image, callback)
    rospy.spin()
