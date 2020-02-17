from __future__ import absolute_import, division, print_function, unicode_literals

import os
import time
import tflite_runtime.interpreter as tflite
import numpy as np
import cv2 as cv

IMAGE_SHAPE = (96, 96)
EDGETPU_SHARED_LIB = 'libedgetpu.so.1'
EDGE_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "../tpu/ohmnilabs_features_extractor_quant_postprocess_edgetpu.tflite")


class HumanTracking:
    def __init__(self):
        self.image_shape = IMAGE_SHAPE
        self.input_shape = IMAGE_SHAPE
        self.interpreter = tflite.Interpreter(
            model_path=EDGE_MODEL,
            experimental_delegates=[
                tflite.load_delegate(EDGETPU_SHARED_LIB)
            ])

    def formaliza_data(self, obj, frame):
        xmin = 0 if obj.bbox.xmin < 0 else obj.bbox.xmin
        xmax = 300 if obj.bbox.xmax > 300 else obj.bbox.xmax
        ymin = 0 if obj.bbox.ymin < 0 else obj.bbox.ymin
        ymax = 300 if obj.bbox.ymax > 300 else obj.bbox.ymax
        box = [xmin/300, ymin/300, xmax/300, ymax/300]
        if xmin == xmax:
            return np.zeros(self.image_shape)
        if ymin == ymax:
            return np.zeros(self.image_shape)
        cropped_obj_img = frame[ymin:ymax, xmin:xmax]
        resized_obj_img = cv.resize(cropped_obj_img, self.image_shape)
        obj_img = resized_obj_img/255.0
        return box, obj_img

    def predict(self, imgs, bboxes):
        estart = time.time()
        features = None
        input_details = self.interpreter.get_input_details()
        output_details = self.interpreter.get_output_details()

        for img in imgs:
            img = np.array(img, dtype=np.float32)
            self.interpreter.allocate_tensors()
            self.interpreter.set_tensor(input_details[0]['index'], [img])
            self.interpreter.invoke()
            feature = self.interpreter.get_tensor(output_details[0]['index'])
            if features is None:
                features = feature
            else:
                features = np.append(features, feature, axis=0)

        bboxes = np.array(bboxes, dtype=np.float32)
        output = np.concatenate((features, bboxes), axis=1)
        eend = time.time()
        print('Extractor estimated time {:.4f}'.format(eend-estart))

        return output
