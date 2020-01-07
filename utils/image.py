from PIL import Image, ImageDraw
import numpy as np
import cv2 as cv
import hashlib


def convert_cv_to_pil(img):
    img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    im_pil = Image.fromarray(img)
    return im_pil


def convert_pil_to_cv(im_pil):
    img = np.asarray(im_pil)
    img = cv.cvtColor(img, cv.COLOR_RGB2BGR)
    return img


def resize(img, size):
    return img.resize(size, Image.ANTIALIAS)


def crop(img, obj):
    return img.crop((obj.bbox.xmin, obj.bbox.ymin, obj.bbox.xmax, obj.bbox.ymax))


def colorize(number):
    color = hashlib.sha1(str(number).encode('utf-8')).hexdigest()
    return "#"+color[-6:]


def draw_objs(img, objs):
    draw = ImageDraw.Draw(img)
    for obj in objs:
        color = colorize(obj.id)
        bbox = obj.bbox
        draw.rectangle([(bbox.xmin, bbox.ymin), (bbox.xmax, bbox.ymax)],
                       outline=color)
        draw.text((bbox.xmin + 10, bbox.ymin + 10),
                  'id: %d\nlabel: %s\nscore: %.2f' % (
                      obj.id, obj.label, obj.score),
                  fill=color)


def draw_box(img, bbox):
    draw = ImageDraw.Draw(img)
    for box in bbox:
        draw.rectangle([(box[0], box[1]), (box[2], box[3])],
                       outline='red')


def draw_point(img, point, color):
    draw = ImageDraw.Draw(img)
    (x, y) = point
    draw.rectangle([(x-2, y-2), (x+2, y+2)],
                   outline=color, fill=color)
