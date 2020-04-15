import os
import tflite_runtime.interpreter as tflite
import cv2 as cv

EDGETPU_SHARED_LIB = 'libedgetpu.so.1'
LABELS = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../models/tpu/coco_labels.txt")
MODELS = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../models/tpu/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite")


class HumanDetection:
    def __init__(self, confidence=0.5):
        self.input_shape = (300, 300)
        self.labels = self.load_labels()
        self.interpreter = tflite.Interpreter(
            model_path=MODELS,
            experimental_delegates=[
                tflite.load_delegate(EDGETPU_SHARED_LIB)
            ])
        self.confidence = confidence
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def load_labels(self):
        with open(LABELS, 'r', encoding='utf-8') as labels_file:
            lines = labels_file.readlines()
            if not lines:
                return {}

            pairs = [line.split(' ', maxsplit=1) for line in lines]
            return {int(index): label.strip() for index, label in pairs}

    def predict(self, img):
        img = cv.resize(img, self.input_shape)
        self.interpreter.allocate_tensors()
        self.interpreter.set_tensor(self.input_details[0]['index'], [img])
        self.interpreter.invoke()
        boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        class_ids = self.interpreter.get_tensor(
            self.output_details[1]['index'])[0]
        scores = self.interpreter.get_tensor(
            self.output_details[2]['index'])[0]
        count = int(self.interpreter.get_tensor(
            self.output_details[3]['index'])[0])

        def make(i):
            ymin, xmin, ymax, xmax = boxes[i]
            return [0, int(class_ids[i]), 0, scores[i], xmin, ymin, xmax, ymax]

        return [make(i) for i in range(count) if (scores[i] >= self.confidence and int(class_ids[i]) == 0)]
