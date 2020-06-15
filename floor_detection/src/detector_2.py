import time
import tflite_runtime.interpreter as tflite
import cv2 as cv
import numpy as np
import os
from skimage.draw import line

EDGETPU_SHARED_LIB = 'libedgetpu.so.1'
OUTPUT_CHANNELS = 2

class FloorDetection:
        def __init__(self, model_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), 
        '../models/tpu/ohmnilabs_floornet_224_quant_postprocess_edgetpu.tflite')):
            self.model_dir = model_dir
            
            self.interpreter = tflite.Interpreter(
                    model_path=self.model_dir,
                    experimental_delegates=[
                        tflite.load_delegate(EDGETPU_SHARED_LIB, {"device": "usb:0"})
                    ])
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()

            self.image_shape = (
                    self.input_details[0]['shape'][1],
                    self.input_details[0]['shape'][2]
            )

           

        def __summary(self):
            print('*** Input details:', self.input_details)
            print('*** Output details:', self.output_details)


        def __normalize(self, img):
            img = cv.resize(img, self.image_shape)
            return np.array(img/255, dtype=np.float32)


        def __create_mask(self, pred_mask):
            pred_mask = np.argmax(pred_mask, axis=-1)
            pred_mask = pred_mask[..., np.newaxis]
            mask = np.reshape(pred_mask, self.image_shape)
            mask = np.array(mask, dtype=np.float32)
            
            return mask
        
        def infer(self, img):
            self.interpreter.allocate_tensors()
            self.interpreter.set_tensor(self.input_details[0]['index'], [img])
            self.interpreter.invoke()
            feature = self.interpreter.get_tensor(self.output_details[0]['index'])
            return np.array(feature[0], dtype=np.float32)

        def predict(self, img):
            estart = time.time()
            img = self.__normalize(img)
            pred_mask = self.infer(img)
            mask = self.__create_mask(pred_mask)
            eend = time.time()
            
            print('Segmentation estimated time {:.4f}'.format(eend-estart))
            return img, mask


class ObstacleAvoidance:
    def __init__(self, mask_img):
        """
        mask_img: binary image (contains black as floor, others as obstacle)
        """

        self.img = mask_img
        self.img_height, self.img_width = self.img.shape[:2]
    
    def check_collide_with_traj(self, traj):
        """
        Input: trajectory: a waypoint which we will consider if any obstacles lying on it.
        Output: Boolean
        """
        def lineLine(line1, line2):
            x1, y1, x2, y2 = line1[0][0], line1[0][1], line1[1][0], line1[1][1]
            x3,y3,x4,y4 = line2[0][0], line2[0][1], line2[1][0], line2[1][1]
            #if y4-y3==0 or x2-x1==0 or x4-x3==0 or y2-y1==0:
                #return False
            if (y4-y3)*(x2-x1) - (x4-x3)*(y2-y1) == 0 or (y4-y3)*(x2-x1) - (x4-x3)*(y2-y1) == 0:
                return False
            uA = ((x4-x3)*(y1-y3) - (y4-y3)*(x1-x3)) / ((y4-y3)*(x2-x1) - (x4-x3)*(y2-y1))
            uB = ((x2-x1)*(y1-y3) - (y2-y1)*(x1-x3)) / ((y4-y3)*(x2-x1) - (x4-x3)*(y2-y1))

            if (uA >= 0 and uA <= 1 and uB >= 0 and uB <= 1):
                return True

            return False
        
        def lineRect(line, rect):
            x1,y1,x2,y2 = line[0][0], line[0][1], line[1][0], line[1][1]
            rx, ry, rw, rh = rect[0], rect[1], rect[2], rect[3]
            left = lineLine(((x1,y1), (x2,y2)), ((rx,ry), (rx, ry+rh)))
            right = lineLine(((x1,y1), (x2,y2)), ((rx+rw, ry), (rx+rw, ry+rh)))
            top = lineLine(((x1,y1), (x2,y2)), ((rx,ry), (rx+rw, ry)))
            bottom = lineLine(((x1,y1), (x2,y2)), ((rx, ry+rh), (rx+rw, ry+rh)))
            if left or right or top or bottom:
                return True
            return False

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
                if self.img[p[1], p[0]] == 255:#white is obstacles
                    return True, boundRect

        return False, boundRect
    
    
    def find_obstacles(self):
        """
        find obstacles using contour method, the height of the obstacles must be higher than half of the image height 
        return a list of obstacles respect to the requirements
        """
        print(self.img.shape)
        threshold = 30
        # Detect edges using Canny
        canny_output = cv.Canny(np.uint8(self.img), threshold, threshold * 2)
        # Find contours
        contours, hierarchy = cv.findContours(canny_output, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        boundRect = []

        for i, c in enumerate(contours):
            tmpRect = cv.boundingRect(cv.approxPolyDP(c,3,True))
            if tmpRect[1] < self.img_height//2:
                boundRect.append(tmpRect)
    
        return boundRect
