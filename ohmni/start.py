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


def detect_gesture(pd, ht, cv_img):
    # Inference
    _, t, status, obj_img, bbox = pd.predict(cv_img)
    # print('Pose detection estimated time {:.4f}'.format(t/1000))
    # Calculate result
    vector = None
    if status != 0:
        (xmin, ymin, xmax, ymax) = bbox
        obj_img = obj_img/255.
        bbox = (int(xmin/pd.image_shape[0]),
                int(ymin/pd.image_shape[1]),
                int(xmax/pd.image_shape[0]),
                int(ymax/pd.image_shape[1]))
        vector = ht.predict([obj_img], [bbox])
    # Return
    return vector


def detect_human(hd, cv_img):
    # Inference
    tpustart = time.time()
    objs = hd.predict(cv_img)
    tpuend = time.time()
    print('Human detection estimated time {:.4f}'.format(tpuend-tpustart))
    # Return
    return objs


def tracking(ht, objs, prev_vector, cv_img):
    # Initialize returned vars
    distances = []
    vectormax = None
    distancemax = None
    argmax = 0
    # Initialize registers
    obj_imgs_batch = []
    bboxes_batch = []
    # Push objects to registers
    for obj in objs:
        box, obj_img = ht.formaliza_data(obj, cv_img)
        obj_imgs_batch.append(obj_img)
        bboxes_batch.append(box)
    # Inference
    vectors = ht.predict(obj_imgs_batch, bboxes_batch)
    # Calculate results
    for index, vector in enumerate(vectors):
        v = vector - prev_vector
        d = np.linalg.norm(v, 2)
        distances.append(d)
        if index == 0:
            vectormax = vector
            distancemax = d
            argmax = index
            continue
        if d < distancemax:
            vectormax = vector
            distancemax = d
            argmax = index
    # Return
    return distances, vectormax, distancemax, argmax


def start(server, botshell):
    pd = PoseDetection()
    hd = HumanDetection()
    ht = HumanTracking()
    ctrl = Controller()

    sm = StateMachine()
    prev_vector = None

    while(True):
        timer = cv.getTickCount()
        pilimg = camera.fetch(server)
        if pilimg is None:
            continue
        img = image.convert_pil_to_cv(pilimg)

        state = sm.get()

        # Wait for an activation (raising hands)
        if state == 'idle':
            # Resize image
            cv_img = cv.resize(img, pd.input_shape)
            # Detect gesture
            prev_vector = detect_gesture(pd, ht, cv_img)
            if prev_vector is None:
                botshell.sendall(b'manual_move 0 0\n')
            else:
                sm.run()
        # Tracking
        if state == 'run':
            # Resize image
            cv_img = cv.resize(img, hd.input_shape)
            # Detect human
            objs = detect_human(hd, cv_img)
            if len(objs) == 0:
                print(f'{sm.state_counter} steps to idle')
                botshell.sendall(b'manual_move 0 0\n')
                sm.idle()
                continue
            # Tracking
            distances, vectormax, distancemax, argmax = tracking(
                ht, objs, prev_vector, cv_img)
            # Show info
            print('*** Euclidean distances:', distances)
            print('*** The minimum distance:', distancemax)
            # Calculate results
            if distancemax < 5:
                sm.run()
                # Assign global vars
                prev_vector = vectormax
                # Drive car
                obj = objs[argmax]
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
                print(f'{sm.state_counter} steps to idle')
                botshell.sendall(b"manual_move 0 0\n")
                sm.idle()
            # Calculate Frames per second (FPS)
            print("Total Estimated Time: ",
                  (cv.getTickCount()-timer)/cv.getTickFrequency())
            fps = cv.getTickFrequency() / (cv.getTickCount() - timer)
            print("FPS: {:.1f}".format(fps))
            print("\n\n")
