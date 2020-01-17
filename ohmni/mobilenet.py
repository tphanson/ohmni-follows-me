from __future__ import absolute_import, division, print_function, unicode_literals

import os
import tflite_runtime.interpreter as tflite
import numpy as np


EDGETPU_SHARED_LIB = 'libedgetpu.so.1'
MODELS = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../tpu/mobilenet_v2_features_extractor_quant_postprocess_edgetpu.tflite")


class Mobilenet():
    def __init__(self):
        self.interpreter = tflite.Interpreter(
            model_path=MODELS,
            experimental_delegates=[
                tflite.load_delegate(EDGETPU_SHARED_LIB)
            ])

    def predict(self, tensor):
        re = None
        input_details = self.interpreter.get_input_details()
        print(input_details)
        output_details = self.interpreter.get_output_details()
        for obj in tensor:
            self.interpreter.allocate_tensors()
            self.interpreter.set_tensor(input_details[0]['index'], [obj])
            self.interpreter.invoke()
            feature = self.interpreter.get_tensor(output_details[0]['index'])
            if re is None:
                re = feature
            else:
                re = np.append(re, feature, axis=0)
        return re
