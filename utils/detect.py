import numpy as np
from utils.bbox import Object, BBox


def input_size(interpreter):
    _, height, width, _ = interpreter.get_input_details()[0]['shape']
    return width, height


def input_tensor(interpreter):
    tensor_index = interpreter.get_input_details()[0]['index']
    return interpreter.tensor(tensor_index)()[0]


def set_input(interpreter, img):
    tensor = input_tensor(interpreter)
    tensor.fill(0)  # padding
    tensor = img


def output_tensor(interpreter, i):
    tensor_index = interpreter.get_output_details()[i]['index']
    tensor = interpreter.tensor(tensor_index)()
    return np.squeeze(tensor)


def get_output(interpreter, score_threshold, human_only=False):
    boxes = output_tensor(interpreter, 0)
    class_ids = output_tensor(interpreter, 1)
    scores = output_tensor(interpreter, 2)
    count = int(output_tensor(interpreter, 3))

    def make(i):
        ymin, xmin, ymax, xmax = boxes[i]
        return Object(
            id=0,
            frame=0,
            label=int(class_ids[i]),
            score=scores[i],
            bbox=BBox(xmin=int(xmin*300),
                      ymin=int(ymin*300),
                      xmax=int(xmax*300),
                      ymax=int(ymax*300)))
    if (human_only):
        return [make(i) for i in range(count) if (scores[i] >= score_threshold and int(class_ids[i]) == 0)]
    else:
        return [make(i) for i in range(count) if (scores[i] >= score_threshold)]
