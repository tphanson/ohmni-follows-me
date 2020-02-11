import time
import cv2 as cv
import numpy as np

from utils import image, camera
from ohmni.humandetection import HumanDetection
from ohmni.tracker import Inference
from ohmni.controller import Controller

# Open camera:
# monkey -p net.sourceforge.opencamera -c android.intent.category.LAUNCHER 1

# RO: 0.00253 rad/s/unit ; unit: (1,1)
# MOV: 0.43 mm/s/unit ; unit: (1,-1)
SLOW_RO = 200
MEDIUM_RO = 350
SLOW_MO = 500
MEDIUM_MO = 1000
FAST_MO = 2500


def start(server, botshell):
    inference = Inference()
    hd = HumanDetection()
    ctrl = Controller()

    prev_vector = None

    while(True):
        print("======================================")
        pilimg = camera.fetch(server)

        if pilimg is None:
            continue

        timer = cv.getTickCount()

        imgstart = time.time()
        img = image.convert_pil_to_cv(pilimg)
        cv_img = cv.resize(img, (300, 300))
        imgend = time.time()
        print('Image estimated time {:.4f}'.format(imgend-imgstart))

        tpustart = time.time()
        objs = hd.predict(cv_img)
        tpuend = time.time()
        print('TPU estimated time {:.4f}'.format(tpuend-tpustart))

        if len(objs) == 0:
            botshell.sendall(b"manual_move 0 0\n")
            continue

        if prev_vector is None:
            obj_id = 0
            if len(objs) <= obj_id:
                continue
            box, obj_img = inference.formaliza_data(objs[obj_id], cv_img)
            prev_vector = inference.predict([obj_img], [box])
        else:
            bboxes_batch = []
            obj_imgs_batch = []

            for obj in objs:
                box, obj_img = inference.formaliza_data(obj, cv_img)
                bboxes_batch.append(box)
                obj_imgs_batch.append(obj_img)

            vectors = inference.predict(obj_imgs_batch, bboxes_batch)
            argmax = 0
            distancemax = None
            vectormax = None
            debug_register = []

            for index, vector in enumerate(vectors):
                v = vector - prev_vector
                d = np.linalg.norm(v, 2)
                debug_register.append(d)
                if index == 0:
                    argmax = index
                    distancemax = d
                    vectormax = vector
                    continue
                if d < distancemax:
                    argmax = index
                    distancemax = d
                    vectormax = vector

            print('*** Object distances:', debug_register)
            print('*** Minimum distance:', distancemax)

            if distancemax < 5:
                prev_vector = vectormax
                obj = objs[argmax]

                # Drive car
                area = (obj.bbox.xmax-obj.bbox.xmin) * \
                    (obj.bbox.ymax-obj.bbox.ymin)
                xmed = (obj.bbox.xmin + obj.bbox.xmax)/2
                print('*** AREA:', area)
                print('*** XMED:', xmed)

                LW, RW = ctrl.calculate(area, xmed)

                # Static test
                print('*** Manual move:', LW, RW)
                # Dynamic test
                botshell.sendall(f"manual_move {LW} {RW}\n".encode())
            else:
                print('*** Manual move:', 0, 0)
                botshell.sendall(b"manual_move 0 0\n")

        # Calculate Frames per second (FPS)
        print("Total Estimated Time: ",
              (cv.getTickCount()-timer)/cv.getTickFrequency())
        fps = cv.getTickFrequency() / (cv.getTickCount() - timer)
        print("FPS: {:.1f}".format(fps))
        print("\n\n")
