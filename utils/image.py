import cv2 as cv
import hashlib


def resize(img, size):
    return cv.resize(img, size)


def crop(img, box):
    [xmin, ymin, xmax, ymax] = box
    return img[ymin:ymax, xmin:xmax]


def colorize(number):
    seed = hashlib.sha1(str(number).encode('utf-8')).hexdigest()
    value = seed[-6:]
    color = tuple(int(value[i:i+2], 16) for i in range(0, 6, 2))
    return color


def draw_objs(img, objs):
    for obj in objs:
        (height, width, _) = img.shape

        xmin = int(obj[-4]*width)
        xmin = 0 if xmin < 0 else xmin
        xmin = width if xmin > width else xmin

        ymin = int(obj[-3]*height)
        ymin = 0 if ymin < 0 else ymin
        ymin = height if ymin > height else ymin

        xmax = int(obj[-2]*width)
        xmax = 0 if xmax < 0 else xmax
        xmax = width if xmax > width else xmax

        ymax = int(obj[-1]*height)
        ymax = 0 if ymax < 0 else ymax
        ymax = height if ymax > height else ymax

        color = colorize(obj[0])
        img = cv.rectangle(img, (xmin, ymin), (xmax, ymax), color, 1)
        img = cv.putText(img, 'id: %d' % (obj[0]), (xmin+10, ymin+10),
                         cv.FONT_HERSHEY_SIMPLEX, 0.3, color, 1, cv.LINE_AA)
        img = cv.putText(img, 'label: %s' % (obj[1]), (xmin+10, ymin+20),
                         cv.FONT_HERSHEY_SIMPLEX, 0.3, color, 1, cv.LINE_AA)
        img = cv.putText(img, 'score: %.2f' % (obj[3]), (xmin+10, ymin+30),
                         cv.FONT_HERSHEY_SIMPLEX, 0.3, color, 1, cv.LINE_AA)

    return img


def draw_box(img, box):
    color = (0, 0, 255)
    [xmin, ymin, xmax, ymax] = box
    img = cv.rectangle(img, (xmin, ymin), (xmax, ymax), color, 1)
    return img
