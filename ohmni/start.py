import time
import cv2 as cv

from utils.ros import ROSImage
from utils import image
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
        bbox = (xmin/pd.image_shape[0], ymin/pd.image_shape[1],
                xmax/pd.image_shape[0], ymax/pd.image_shape[1])
        vector = ht.predict([obj_img], [bbox], True)
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


def tracking(ht, objs, cv_img):
    # Initialize registers
    obj_imgs_batch = []
    bboxes_batch = []
    # Push objects to registers
    for obj in objs:
        box, obj_img = ht.formaliza_data(obj, cv_img)
        obj_imgs_batch.append(obj_img)
        bboxes_batch.append(box)
    # Inference
    return ht.predict(obj_imgs_batch, bboxes_batch)


def start(botshell):
    rosimg = ROSImage()
    rosimg.start()

    pd = PoseDetection()
    hd = HumanDetection()
    ht = HumanTracking()
    ctrl = Controller(hd.input_shape, NECK_POS)

    sm = StateMachine()

    while(True):
        fpsstart = time.time()
        state = sm.get_state()
        print('Debug:', state)

        header, img = rosimg.get()

        if img is None:
            pass
        else:
            # Stop
            if state == 'init_idle':
                print('*** Manual move:', 0, 0)
                botshell.sendall(b'manual_move 0 0\n')
                botshell.sendall(
                    f'neck_angle {NECK_POS}\n'.encode())
                ht.reset()
                sm.next_state(True)
            # Wait for an activation (raising hands)
            if state == 'idle':
                # Resize image
                cv_img = cv.resize(img, pd.input_shape)
                # Detect gesture
                vector = detect_gesture(pd, ht, cv_img)
                sm.next_state(vector is not None)
            # Run
            if state == 'init_run':
                sm.next_state(True)
            # Tracking
            if state == 'run':
                # Resize image
                cv_img = cv.resize(img, hd.input_shape)
                pil_img = image.convert_cv_to_pil(cv_img)
                # Detect human
                objs = detect_human(hd, cv_img)
                if len(objs) == 0:
                    print('*** Manual move:', 0, 0)
                    botshell.sendall(b'manual_move 0 0\n')
                    sm.next_state(True)
                else:
                    # Tracking
                    confidences, argmax = tracking(ht, objs, cv_img)
                    print('*** Confidences:', confidences)
                    # Under threshold
                    if argmax is None:
                        print('*** Manual move:', 0, 0)
                        botshell.sendall(b'manual_move 0 0\n')
                        sm.next_state(True)
                    else:
                        # Calculate results
                        sm.next_state(False)
                        # Drive car
                        obj = objs[argmax]
                        LW, RW = ctrl.wheel(obj.bbox)
                        POS = ctrl.neck(obj.bbox)
                        # Static test
                        print('*** Manual move:', LW, RW)
                        print('*** Neck position:', POS)
                        # Dynamic test
                        botshell.sendall(f'manual_move {LW} {RW}\n'.encode())
                        botshell.sendall(f'neck_angle {POS}\n'.encode())
                        # Draw bounding box of tracking objective
                        image.draw_objs(pil_img, [obj])
                        drawed_cv_img = image.convert_pil_to_cv(pil_img)
                        rosimg.push(header, drawed_cv_img)

        # Calculate frames per second (FPS)
        fpsend = time.time()
        delay = 0.05 - fpsend + fpsstart
        if delay > 0:
            time.sleep(delay)
        fpsadjust = time.time()
        print('Total estimated time {:.4f}'.format(fpsend-fpsstart))
        print("FPS: {:.1f} \n\n".format(1 / (fpsadjust-fpsstart)))
