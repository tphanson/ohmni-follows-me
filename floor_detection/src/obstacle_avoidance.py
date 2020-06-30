import cv2 as cv
import numpy as np
import os
from skimage.draw import line

class ObstacleAvoidance:
    def __init__(self, mask_img):
        """
        mask_img: binary image (contains black as floor, others as obstacle)
        """
        self.img = mask_img
        self.img_height, self.img_width = self.img.shape[:2]
    
    def check_collide_with_traj(self, traj, boundRect=None):
        """
        Input: trajectory: a waypoint which we will consider if any obstacles lying on it.
                boundRect: Obstacle (optional)
        Output: Boolean
        """
        def lineLine(line1, line2):
            """
            check intersection between 2 lines
            """
            x1, y1, x2, y2 = line1[0][0], line1[0][1], line1[1][0], line1[1][1]
            x3,y3,x4,y4 = line2[0][0], line2[0][1], line2[1][0], line2[1][1]

            if (y4-y3)*(x2-x1) - (x4-x3)*(y2-y1) == 0 or (y4-y3)*(x2-x1) - (x4-x3)*(y2-y1) == 0:
                return False
            uA = ((x4-x3)*(y1-y3) - (y4-y3)*(x1-x3)) / ((y4-y3)*(x2-x1) - (x4-x3)*(y2-y1))
            uB = ((x2-x1)*(y1-y3) - (y2-y1)*(x1-x3)) / ((y4-y3)*(x2-x1) - (x4-x3)*(y2-y1))

            if (uA >= 0 and uA <= 1 and uB >= 0 and uB <= 1):
                return True

            return False

        def lineRect(line, rect):
            """
            check intersection between a line and a rectangle
            """
            x1,y1,x2,y2 = line[0][0], line[0][1], line[1][0], line[1][1]
            rx, ry, rw, rh = rect[0], rect[1], rect[2], rect[3]
            left = lineLine(((x1,y1), (x2,y2)), ((rx,ry), (rx, ry+rh)))
            right = lineLine(((x1,y1), (x2,y2)), ((rx+rw, ry), (rx+rw, ry+rh)))
            top = lineLine(((x1,y1), (x2,y2)), ((rx,ry), (rx+rw, ry)))
            bottom = lineLine(((x1,y1), (x2,y2)), ((rx, ry+rh), (rx+rw, ry+rh)))
            if left or right or top or bottom:
                return True
            return False

        if boundRect is None: #if have not had obstacle yet
            boundRect=self.find_obstacles()

        for rect in boundRect:
            rx, ry, rw, rh = rect[0], rect[1], rect[2], rect[3]
            for i in range(len(traj) - 1):
                x1, y1, x2, y2 = traj[i][0], traj[i][1], traj[i+1][0], traj[i+1][1]
                if lineRect(((x1, y1), (x2, y2)), rect):
                    return True, boundRect
        
        for i in range(len(traj)-1):
            start = (int(traj[i][0]), int(traj[i][1]))
            end = (int(traj[i+1][0]), int(traj[i+1][1]))
            discrete_line = list(zip(*line(*start, *end)))
            for p in discrete_line:
                if self.img[p[1]-1, p[0]-1] == 255:#white is obstacles
                    return True, boundRect
        
        return False, boundRect
    
    def find_obstacles(self):
        """
        find obstacles using contour method, the height of the obstacles must be higher than half of the image height 
        return a list of obstacles respect to the requirements
        """
        threshold = 30
        # Detect edges using Canny
        canny_output = cv.Canny(np.uint8(self.img), threshold, threshold * 2)
        # Find contours
        contours, hierarchy = cv.findContours(canny_output, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        boundRect = []

        for i, c in enumerate(contours):
            tmpRect = cv.boundingRect(cv.approxPolyDP(c,3,True))
            if tmpRect[1] < self.img_height//2-10 and tmpRect[1] + tmpRect[3] < self.img_height//2-10:
                boundRect.append(tmpRect)

        return boundRect
