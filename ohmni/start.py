import time
import numpy as np
from utils.ros import ROSImage
from utils import image
from detection.posenet import PoseDetection
from detection.coco import HumanDetection
from tracker.triplet import HumanTracking, formaliza_data
from ohmni.controller import Controller
from ohmni.state import StateMachine

# Open camera:
# monkey -p net.sourceforge.opencamera -c android.intent.category.LAUNCHER 1

# Ohmni global config
NECK_POS = 500


def detect_gesture(pd, tracker, img, action='activate'):
    # Inference
    objs, t, status, box = pd.predict(img)
    print('Gesture detection estimated time {:.4f}'.format(t))
    # Calculate result
    ok = False
    if action == 'activate' and (status == 1 or status == 2):
        height, width, _ = img.shape
        xmin, ymin = int(box[0]*width), int(box[1]*height)
        xmax, ymax = int(box[2]*width), int(box[3]*height)
        box = np.array([xmin, ymin, xmax, ymax])
        obj_img = image.crop(img, box)
        obj_img = image.resize(obj_img, tracker.input_shape)
        obj_img = np.array(obj_img/127.5 - 1, dtype=np.float32)
        ok = tracker.set_anchor(obj_img, box)
    if action == 'deactivate' and status == 3:
        ok = True
    # Return
    return ok


def detect_human(hd, img):
    # Inference
    start_time = time.time()
    objs = hd.predict(img)
    print('Human detection estimated time {:.4f}'.format(
        time.time()-start_time))
    # Return
    return objs


def tracking(tracker, objs, img):
    # Initialize registers
    start_time = time.time()
    imgs_batch = []
    bboxes_batch = []
    # Push objects to registers
    for obj in objs:
        obj_img, box = formaliza_data(obj, img)
        imgs_batch.append(obj_img)
        bboxes_batch.append(box)
    print('Tracking estimated time {:.4f}'.format(time.time()-start_time))
    # Inference
    confidences, argmax = tracker.predict(imgs_batch, bboxes_batch)
    print('*** Confidences:', confidences)
    if argmax is None:
        return None
    return bboxes_batch[argmax]


def start(botshell):
    rosimg = ROSImage()
    rosimg.start()

    pd = PoseDetection()
    hd = HumanDetection()
    ht = HumanTracking()
    ctrl = Controller((480, 640), NECK_POS)

    sm = StateMachine()

    while(True):
        fpsstart = time.time()
        state = sm.get_state()
        print('Debug:', state)

        header, img = rosimg.get()

        if img is not None:
            # Stop
            if state == 'init_idle':
                print('*** Manual move:', 0, 0)
                botshell.sendall(b'manual_move 0 0\n')
                botshell.sendall(f'neck_angle {NECK_POS}\n'.encode())
                ht.reset()
                sm.next_state(True)

            # Wait for an activation (raising hands)
            if state == 'idle':
                # Detect gesture
                ok = detect_gesture(pd, ht, img, 'activate')
                sm.next_state(ok)

            # Run
            if state == 'init_run':
                sm.next_state(True)

            # Tracking
            if state == 'run':
                # Detect human
                objs = detect_human(hd, img)
                if len(objs) == 0:
                    print('*** Manual move:', 0, 0)
                    botshell.sendall(b'manual_move 0 0\n')
                    sm.next_state(True)
                else:
                    # Tracking
                    box = tracking(ht, objs, img)
                    # Under threshold
                    if box is None:
                        print('*** Manual move:', 0, 0)
                        botshell.sendall(b'manual_move 0 0\n')
                        sm.next_state(True)
                    else:
                        # Calculate results
                        sm.next_state(False)
                        # Drive car
                        LW, RW = ctrl.wheel(box)
                        POS = ctrl.neck(box)
                        # Static test
                        print('*** Manual move:', LW, RW)
                        print('*** Neck position:', POS)
                        # Dynamic test
                        botshell.sendall(f'manual_move {LW} {RW}\n'.encode())
                        botshell.sendall(f'neck_angle {POS}\n'.encode())
                        # Draw bounding box of tracking objective
                        img = image.draw_box(img, box)
                        rosimg.apush(header, img)

        # Calculate frames per second (FPS)
        fpsend = time.time()
        delay = 0.05 - fpsend + fpsstart
        if delay > 0:
            time.sleep(delay)
        fpsadjust = time.time()
        print('Total estimated time {:.4f}'.format(fpsend-fpsstart))
        print("FPS: {:.1f} \n\n".format(1 / (fpsadjust-fpsstart)))
