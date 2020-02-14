import time
import cv2 as cv
import numpy as np

from utils import image, camera
from detection.posenet import PoseDetection
from detection.coco import HumanDetection
from tracker.triplet import HumanTracking
from ohmni.controller import Controller
from ohmni.state import StateMachine

# Open camera:
# monkey -p net.sourceforge.opencamera -c android.intent.category.LAUNCHER 1


def detect_activation(pd, ht, img):
    cv_img = cv.resize(img, pd.input_shape)
    _, t, status, obj_img, bbox = pd.predict(cv_img)
    print('Pose detection estimated time {:.4f}'.format(t/1000))

    vector = None
    if status != 0:
        (xmin, ymin, xmax, ymax) = bbox
        bbox = (int(xmin*300/pd.image_shape[0]),
                int(ymin*300/pd.image_shape[1]),
                int(xmax*300/pd.image_shape[0]),
                int(ymax*300/pd.image_shape[1]))
        vector = ht.predict([obj_img], [bbox])
    return vector


def tracking(hd, ht):
    pass


def start(server, botshell):
    pd = PoseDetection()
    hd = HumanDetection()
    ht = HumanTracking()
    ctrl = Controller()

    sm = StateMachine()
    prev_vector = None

    while(True):
        print("======================================")
        pilimg = camera.fetch(server)
        if pilimg is None:
            continue
        img = image.convert_pil_to_cv(pilimg)

        timer = cv.getTickCount()
        state = sm.get()

        # Wait for an activation (raising hands)
        if state == 'idle':
            prev_vector = detect_activation(pd, ht, img)
            if prev_vector is None:
                botshell.sendall(b'manual_move 0 0\n')
            else:
                sm.next()

        # Tracking
        if state == 'run' or state == 'wait':

            imgstart = time.time()
            cv_img = cv.resize(img, (300, 300))
            imgend = time.time()
            print('Image estimated time {:.4f}'.format(imgend-imgstart))

            tpustart = time.time()
            objs = hd.predict(cv_img)
            tpuend = time.time()
            print('Human detection estimated time {:.4f}'.format(
                tpuend-tpustart))

            if len(objs) == 0:
                botshell.sendall(b"manual_move 0 0\n")
                continue

            obj_imgs_batch = []
            bboxes_batch = []

            for obj in objs:
                box, obj_img = ht.formaliza_data(obj, cv_img)
                obj_imgs_batch.append(obj_img)
                bboxes_batch.append(box)

            vectors = ht.predict(obj_imgs_batch, bboxes_batch)
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
