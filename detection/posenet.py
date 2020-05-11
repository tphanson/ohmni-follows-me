import numpy as np

from utils.pose_engine import PoseEngine
import cv2 as cv

# 'nose','left eye','right eye','left ear','right ear',
# 'left shoulder','right shoulder','left elbow','right elbow','left wrist','right wrist',
# 'left hip','right hip','left knee','right knee','left ankle','right ankle'


class PoseDetection():
    def __init__(self):
        self.engine = PoseEngine(
            'tpu/posenet_mobilenet_v1_075_481_641_quant_decoder_edgetpu.tflite')
        self.raising_confidence = 2
        self.pose_confidence = 0.3
        self.image_shape = (640, 480)
        self.input_shape = (641, 481)

    def generate_bbox(self, marks):
        xmin, ymin, xmax, ymax = self.image_shape[0], self.image_shape[1], 0, 0
        for (_, _, x, y) in marks:
            xmin = min(int(x), xmin)
            ymin = min(int(y), ymin)
            xmax = max(int(x), xmax)
            ymax = max(int(y), ymax)
        box = np.array([
            xmin/self.input_shape[0],
            ymin/self.input_shape[1],
            xmax/self.input_shape[0],
            ymax/self.input_shape[1]],
            dtype=np.float32)
        return box

    def looking_eyes(self, marks):
        looking = 0
        for (label, score, _, _) in marks:
            if label == 'left eye' and score >= self.pose_confidence:
                looking += 1
            if label == 'right eye' and score >= self.pose_confidence:
                looking += 1
        return looking == 2

    def raise_left_hand(self, marks):
        dx, dy = 0, 0
        both = 0
        for (label, score, x, y) in marks:
            if label == 'left elbow' and score >= self.pose_confidence:
                dx += x
                dy += y
                both += 1
            if label == 'left wrist' and score >= self.pose_confidence:
                dx -= x
                dy -= y
                both += 1
        if both == 2:
            print('*** Debug: (left hand)', dy/(abs(dx)+1))
        return both == 2 and dy/(abs(dx)+1) > self.raising_confidence

    def raise_right_hand(self, marks):
        dx, dy = 0, 0
        both = 0
        for (label, score, x, y) in marks:
            if label == 'right elbow' and score >= self.pose_confidence:
                dx += x
                dy += y
                both += 1
            if label == 'right wrist' and score >= self.pose_confidence:
                dx -= x
                dy -= y
                both += 1
        if both == 2:
            print('*** Debug: (right hand)', dy/(abs(dx)+1))
        return both == 2 and dy/(abs(dx)+1) > self.raising_confidence

    def activate(self, marks):
        print("===================================")
        print(self.looking_eyes(marks), self.raise_right_hand(
            marks), self.raise_left_hand(marks))
        if self.looking_eyes(marks) and self.raise_left_hand(marks) and self.raise_right_hand(marks):
            box = self.generate_bbox(marks)
            print(3)
            return 3, box
        elif self.looking_eyes(marks) and self.raise_left_hand(marks):
            box = self.generate_bbox(marks)
            print(2)
            return 2, box
        elif self.looking_eyes(marks) and self.raise_right_hand(marks):
            box = self.generate_bbox(marks)
            print(1)
            return 1, box
        else:
            print(0)
            return 0, np.array([0., 0., 0., 0.], dtype=np.float32)

    def inference(self, img):
        poses, inference_time = self.engine.DetectPosesInImage(img)
        objects = []
        for pose in poses:
            if pose.score < self.pose_confidence:
                continue
            marks = []
            for label, keypoint in pose.keypoints.items():
                x = keypoint.yx[1]
                y = keypoint.yx[0]
                score = keypoint.score
                marks.append((label, score, x, y))
            objects.append(marks)
        return objects, inference_time

    def predict(self, img):
        img = cv.resize(img, self.input_shape)
        objects, inference_time = self.inference(img)

        status = 0
        box = None
        for marks in objects:
            # Find an activation
            status, box = self.activate(marks)
            if status != 0:
                break 
        return objects, inference_time, status, box
