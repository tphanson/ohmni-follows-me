import time
import cv2 as cv
import numpy as np

# from utils import camera
from utils.camera import Camera
from detection.posenet import PoseDetection
from detection.coco import HumanDetection
from tracker.triplet import HumanTracking
from ohmni.controller import Controller
from ohmni.state import StateMachine

# Open camera:
# monkey -p net.sourceforge.opencamera -c android.intent.category.LAUNCHER 1

# Ohmni global config
NECK_POS = 500


def detect_gesture(pd, ht, cv_img):
    # Inference
    _, t, status, obj_img, bbox = pd.predict(cv_img)
    print('Gesture detection estimated time {:.4f}'.format(t))
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


def start(botshell):
    cam = Camera()
    cam.start_server()

    pd = PoseDetection()
    hd = HumanDetection()
    ht = HumanTracking()
    ctrl = Controller(hd.input_shape, NECK_POS)

    sm = StateMachine()
    prev_vector = None

    while(True):
        fpsstart = time.time()
        state = sm.get_state()
        print('Debug:', state)

        imgstart = time.time()
        img = cam.fetch()
        imgend = time.time()
        print('Image estimated time {:.4f}'.format(imgend-imgstart))
        if img is None:
            pass
        else:
            # Stop
            if state == 'init_idle':
                print('*** Manual move:', 0, 0)
                botshell.sendall(b'manual_move 0 0\n')
                botshell.sendall(
                    f'neck_angle {NECK_POS}\n'.encode())
                sm.next_state(True)
            # Wait for an activation (raising hands)
            if state == 'idle':
                # Resize image
                cv_img = cv.resize(img, pd.input_shape)
                # Detect gesture
                vector = detect_gesture(pd, ht, cv_img)
                sm.next_state(vector is not None)
                if vector is not None:
                    prev_vector = vector
            # Run
            if state == 'init_run':
                sm.next_state(True)
            # Tracking
            if state == 'run':
                # Resize image
                cv_img = cv.resize(img, hd.input_shape)
                # Detect human
                objs = detect_human(hd, cv_img)
                if len(objs) == 0:
                    print('*** Manual move:', 0, 0)
                    botshell.sendall(b'manual_move 0 0\n')
                    sm.next_state(True)
                else:
                    # Tracking
                    distances, vectormax, distancemax, argmax = tracking(
                        ht, objs, prev_vector, cv_img)
                    # Show info
                    print('*** Euclidean distances:', distances)
                    print('*** The minimum distance:', distancemax)
                    # Under threshold
                    if distancemax > 5:
                        print('*** Manual move:', 0, 0)
                        botshell.sendall(b'manual_move 0 0\n')
                        sm.next_state(True)
                    else:
                        # Calculate results
                        sm.next_state(False)
                        prev_vector = vectormax
                        # Drive car
                        obj = objs[argmax]
                        LW, RW = ctrl.wheel(obj.bbox)
                        POS = ctrl.neck(obj.bbox)
                        # Static test
                        print('*** Manual move:', LW, RW)
                        print('*** Neck position:', POS)
                        # Dynamic test
                        # botshell.sendall(f'manual_move {LW} {RW}\n'.encode())
                        botshell.sendall(f'neck_angle {POS}\n'.encode())

        # Calculate frames per second (FPS)
        fpsend = time.time()
        delay = 0.05 - fpsend + fpsstart
        if delay > 0:
            time.sleep(delay)
        fpsadjust = time.time()
        print('Total estimated time {:.4f}'.format(fpsend-fpsstart))
        print("FPS: {:.1f} \n\n".format(1 / (fpsadjust-fpsstart)))
