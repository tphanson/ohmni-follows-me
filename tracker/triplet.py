from __future__ import absolute_import, division, print_function, unicode_literals

import os
import time
import tflite_runtime.interpreter as tflite
import numpy as np
import cv2 as cv

IMAGE_SHAPE = (160, 160)
EDGETPU_SHARED_LIB = 'libedgetpu.so.1'
EDGE_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "../tpu/ohmnilabs_features_extractor_quant_postprocess_edgetpu.tflite")


def formaliza_data(obj, frame):
    start = time.time()
    (height, width, _) = frame.shape

    xmin = min(width, max(0, int(obj[-4]*width)))
    ymin = min(height, max(0, int(obj[-3]*height)))
    xmax = min(width, max(0, int(obj[-2]*width)))
    ymax = min(height, max(0, int(obj[-1]*height)))

    box = [xmin, ymin, xmax, ymax]
    if xmin >= xmax or ymin >= ymax:
        return np.zeros(IMAGE_SHAPE), box

    cropped_obj_img = frame[ymin:ymax, xmin:xmax]
    resized_obj_img = cv.resize(cropped_obj_img, IMAGE_SHAPE)
    obj_img = np.array(resized_obj_img/127.5 - 1, dtype=np.float32)
    return obj_img, box


class HumanTracking:
    def __init__(self, confidence=0.7, threshold=35):
        self.input_shape = IMAGE_SHAPE
        self.interpreter = tflite.Interpreter(
            model_path=EDGE_MODEL,
            experimental_delegates=[
                tflite.load_delegate(EDGETPU_SHARED_LIB)
            ])
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.confidence = confidence
        self.threshold = threshold
        self.prev_encoding = None
        self.prev_bbox = None

    def reset(self):
        self.prev_encoding = None
        self.prev_bbox = None

    def __area(self, box):
        return max(0, box[3]-box[1]+1)*max(0, box[2]-box[0]+1)

    def __confidence_level(self, distances):
        if len(distances) == 0:
            return np.array([]), None
        deltas = (self.threshold - distances)/self.threshold
        zeros = np.zeros(deltas.shape, dtype=np.float32)
        logits = np.maximum(deltas, zeros)
        logits_sum = np.sum(logits)
        if logits_sum == 0:
            return zeros, None
        else:
            confidences = logits/logits_sum
            return confidences, np.argmax(confidences)

    def iou(self, anchor_box, predicted_box):
        xmin = max(anchor_box[0], predicted_box[0])
        ymin = max(anchor_box[1], predicted_box[1])
        xmax = min(anchor_box[2], predicted_box[2])
        ymax = min(anchor_box[3], predicted_box[3])
        inter_area = self.__area([xmin, ymin, xmax, ymax])
        anchor_area = self.__area(anchor_box)
        predicted_area = self.__area(predicted_box)
        return inter_area/float(anchor_area+predicted_area-inter_area)

    def infer(self, img):
        self.interpreter.allocate_tensors()
        self.interpreter.set_tensor(
            self.input_details[0]['index'], [list(img)])
        self.interpreter.invoke()
        feature = self.interpreter.get_tensor(self.output_details[0]['index'])
        print(feature[0].dtype)
        return np.array(feature[0], dtype=np.float32)

    def set_anchor(self, img, bbox):
        encoding = self.infer(img)
        self.prev_encoding = encoding
        self.prev_bbox = bbox
        return True

    def predict(self, imgs, bboxes):
        estart = time.time()

        differentials = np.array([])
        indice = []
        encodings = []
        for index, box in enumerate(bboxes):
            iou = self.iou(self.prev_bbox, box)
            if iou > 0.5:
                img = imgs[index]
                encoding = self.infer(img)
                differential = np.linalg.norm(
                    self.prev_encoding - encoding)

                differentials = np.append(differentials, differential)
                indice.append(index)
                encodings.append(encoding)

        print('Differentials:', differentials)

        confidences, argmax = self.__confidence_level(differentials)
        index = indice[argmax] if argmax is not None else None

        eend = time.time()
        print('Extractor estimated time {:.4f}'.format(eend-estart))
        if argmax is not None and confidences[argmax] > self.confidence:
            self.prev_encoding = encodings[argmax]
            self.prev_bbox = bboxes[index]
        return confidences, index
