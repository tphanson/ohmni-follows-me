import os
import tflite_runtime.interpreter as tflite
import cv2 as cv

from utils import detect

EDGETPU_SHARED_LIB = 'libedgetpu.so.1'
LABELS = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../tpucoco/coco_labels.txt")
MODELS = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../tpucoco/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite")


class HumanDetection:
    def __init__(self, confidence=0.6):
        self.labels = self.load_labels()
        self.interpreter = self.make_interpreter(MODELS)
        self.confidence = confidence

    def load_labels(self):
        with open(LABELS, 'r', encoding='utf-8') as labels_file:
            lines = labels_file.readlines()
            if not lines:
                return {}

            pairs = [line.split(' ', maxsplit=1) for line in lines]
            return {int(index): label.strip() for index, label in pairs}

    def make_interpreter(self, models):
        return tflite.Interpreter(
            model_path=models,
            experimental_delegates=[
                tflite.load_delegate(EDGETPU_SHARED_LIB)
            ])

    def predict(self, img):
        self.interpreter.allocate_tensors()
        scale = detect.set_input(self.interpreter, img.shape,
                                 lambda size: cv.resize(img, size))
        self.interpreter.invoke()
        objs = detect.get_output(
            self.interpreter, self.confidence, scale, True)
        return objs
