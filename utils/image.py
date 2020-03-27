import cv2 as cv


def resize(img, shape):
    return cv.resize(img, shape)

def draw_objs(img, objs):
    for obj in objs:
        bbox = obj.bbox
        img = cv.rectangle(img, (bbox.xmin, bbox.ymin), (bbox.xmax, bbox.ymax),
                           (255, 0, 0), thickness=1)
    return img


def draw_box(img, bbox):
    for box in bbox:
        img = cv.rectangle(img, (box[0], box[1]), (box[2], box[3]),
                           (255, 0, 0), thickness=1)
    return img
