from __future__ import absolute_import, division, print_function, unicode_literals

import os
import time
import tflite_runtime.interpreter as tflite
import numpy as np
from utils import image

IMAGE_SHAPE = (96, 96)
EDGETPU_SHARED_LIB = 'libedgetpu.so.1'
EDGE_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "../tpu/ohmnilabs_features_extractor_quant_postprocess_edgetpu.tflite")


class HumanTracking:
    def __init__(self):
        self.frame_shape = (300, 300)
        self.image_shape = IMAGE_SHAPE
        self.input_shape = IMAGE_SHAPE
        self.interpreter = tflite.Interpreter(
            model_path=EDGE_MODEL,
            experimental_delegates=[
                tflite.load_delegate(EDGETPU_SHARED_LIB)
            ])
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.confidence = 0.7
        self.threshold = 8
        self.tradeoff = 10  # Between encoding distance and bbox distance
        self.prev_encoding = None
        self.prev_bbox = None

    def reset(self):
        self.prev_encoding = None
        self.prev_bbox = None

    def formaliza_data(self, obj, frame):
        xmin = 0 if obj.bbox.xmin < 0 else obj.bbox.xmin
        xmax = self.frame_shape[0] if obj.bbox.xmax > self.frame_shape[0] else obj.bbox.xmax
        ymin = 0 if obj.bbox.ymin < 0 else obj.bbox.ymin
        ymax = self.frame_shape[1] if obj.bbox.ymax > self.frame_shape[1] else obj.bbox.ymax
        box = np.array([xmin/self.frame_shape[0], ymin/self.frame_shape[1],
                        xmax/self.frame_shape[0], ymax/self.frame_shape[1]])
        if xmin == xmax:
            return np.zeros(self.image_shape)
        if ymin == ymax:
            return np.zeros(self.image_shape)
        cropped_obj_img = frame[ymin:ymax, xmin:xmax]
        resized_obj_img = image.resize(cropped_obj_img, self.image_shape)
        obj_img = resized_obj_img/255.0
        return box, obj_img

    def confidence_level(self, distances):
        deltas = (self.threshold - distances)/self.threshold
        zeros = np.zeros(deltas.shape, dtype=np.float32)
        logits = np.maximum(deltas, zeros)
        logits_sum = np.sum(logits)
        if logits_sum == 0:
            return zeros
        else:
            confidences = logits/logits_sum
            return confidences

    def infer(self, img):
        img = np.array(img, dtype=np.float32)
        self.interpreter.allocate_tensors()
        self.interpreter.set_tensor(self.input_details[0]['index'], [img])
        self.interpreter.invoke()
        feature = self.interpreter.get_tensor(self.output_details[0]['index'])
        return np.array(feature[0])

    def predict(self, imgs, bboxes, init=False):
        if init:
            if len(imgs) != 1 or len(bboxes) != 1:
                raise ValueError('You must initialize one object only.')
            encoding = self.infer(imgs[0])
            self.prev_encoding = encoding
            self.prev_bbox = bboxes[0]
            return np.array([.0]), 0
        else:
            estart = time.time()
            encodings = []
            features = np.array([])
            positions = np.array([])

            for index, bbox in enumerate(bboxes):
                # Appreance
                img = imgs[index]
                encoding = self.infer(img)
                encodings.append(encoding)
                feature = np.linalg.norm(self.prev_encoding - encoding)
                features = np.append(features, feature)
                # Position
                position = np.linalg.norm(
                    self.prev_bbox - bbox) * self.tradeoff
                positions = np.append(positions, position)

            distances = features + positions
            confidences = self.confidence_level(distances)
            _argmax = np.argmax(confidences)
            argmax = None
            if confidences[_argmax] > self.confidence:
                self.prev_encoding = encodings[_argmax]
                self.prev_bbox = bboxes[_argmax]
                argmax = _argmax

            eend = time.time()
            print('Features:', features)
            print('Positions:', positions)
            print('Distances:', distances)
            print('Extractor estimated time {:.4f}'.format(eend-estart))
            return confidences, argmax
