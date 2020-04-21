import time
import numpy as np
from utils import image, camera
from detection.posenet import PoseDetection
from detection.coco import HumanDetection
from tracker.triplet import HumanTracking, formalize_data
from ohmni.controller import Controller
from ohmni.state import StateMachine

# Open camera:
# monkey -p net.sourceforge.opencamera -c android.intent.category.LAUNCHER 1


def detect_gesture(pd, tracker, img, action='activate'):
    # Inference
    _, t, status, box = pd.predict(img)
    print('Gesture detection estimated time {:.4f}'.format(t/1000))
    # Calculate result
    ok = False
    # 0: None, 1: lefthand, 2: righthand, 3: both hands
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
        obj_img, box = formalize_data(obj, img)
        imgs_batch.append(obj_img)
        bboxes_batch.append(box)
    print('Tracking estimated time {:.4f}'.format(time.time()-start_time))
    # Inference
    confidences, argmax = tracker.predict(imgs_batch, bboxes_batch)
    print('*** Confidences:', confidences)
    if argmax is None:
        return None
    return bboxes_batch[argmax]


def start(server, botshell):
    pd = PoseDetection()
    hd = HumanDetection()
    ht = HumanTracking()

    ctrl = Controller((1024, 1280), botshell)
    ctrl.start()

    sm = StateMachine()

    while True:
        pilimg = camera.fetch(server)
        if pilimg is None:
            time.sleep(0.05)
            continue

        fpsstart = time.time()
        state = sm.get_state()
        print('Debug:', state)

        imgstart = time.time()
        img = np.asarray(pilimg)
        imgend = time.time()
        print('Image estimated time {:.4f}'.format(imgend-imgstart))

        # Stop
        if state == 'init_idle':
            ctrl.stop()
            ht.reset()
            sm.next_state(True, 0.5)

        # Wait for an activation (raising hands)
        if state == 'idle':
            # Detect gesture
            ok = detect_gesture(pd, ht, img, 'activate')
            sm.next_state(ok, 0.5)

        # Run
        if state == 'init_run':
            sm.next_state(True, 0.5)

        # Tracking
        if state == 'run':
            # Detect gesture
            ok = detect_gesture(pd, ht, img, 'deactivate')
            # Detect human
            objs = detect_human(hd, img)
            # Handle state
            if ok:
                ctrl.wait()
                sm.next_state(True, 0.5)
            elif len(objs) == 0:
                ctrl.wait()
                sm.next_state(True, 5)
            else:
                # Tracking
                box = tracking(ht, objs, img)
                # Under threshold
                if box is None:
                    ctrl.wait()
                    sm.next_state(True, 5)
                else:
                    # Calculate results
                    sm.next_state(False)
                    # Drive car
                    ctrl.goto(box)

        # Calculate frames per second (FPS)
        fpsend = time.time()
        delay = 0.05 - fpsend + fpsstart
        if delay > 0:
            time.sleep(delay)
        fpsadjust = time.time()
        print('Total estimated time {:.4f}'.format(fpsend-fpsstart))
        print('FPS: {:.1f} \n\n'.format(1 / (fpsadjust-fpsstart)))

    ctrl.stop()
    print('Stopped OFM.')