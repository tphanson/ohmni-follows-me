import time
import numpy as np
from utils.thread_camera import CamThread
from utils.spline import approximate_b_spline_path, interpolate_b_spline_path
from utils import image, camera, ros
from detection.posenet import PoseDetection
from detection.coco import HumanDetection
from tracker.triplet import HumanTracking, formalize_data

from floor_detection.src.floor_detection import FloorDetection
from floor_detection.src.trajectory_planner import TrajectoryPlanner
from floor_detection.src.obstacle_avoidance import ObstacleAvoidance

from ohmni.controller import Notifier, Heteronomy, Autonomy
from ohmni.state import StateMachine

from queue import Queue
from threading import Thread

import base64
import zmq
import cv2
#server to stream to the laptop to visualize
context = zmq.Context()
footage_socket = context.socket(zmq.PUB)
ip = "tcp://192.168.123.42:5555"
footage_socket.connect(ip)

# Open camera:
# monkey -p net.sourceforge.opencamera -c android.intent.category.LAUNCHER 1

def detect_floor(fd, img):
    _, mask = fd.predict(img)
    return mask

def stop_motion(mask, v_left, v_right, x, y, theta, limit_time):
    theta = 0
    sample_time = 0.1
    l = 0.333
    #predict left, right and center trajectories
    n_course_point = 20
    q=Queue()
    def predict_traj_direction(direction, x,y):
        predicted_traj = TrajectoryPlanner(x,y,v_left,v_right,theta,l,sample_time)
        predicted_traj.run(v_right, v_left, limit_time)
        path_x, path_y = predicted_traj.path_x, predicted_traj.path_y
        #path_x, path_y = interpolate_b_spline_path(predicted_traj.path_x, predicted_traj.path_y, n_course_point)
        traj = [(i,j) for i, j in zip(path_x, path_y)]
        q.put([direction, traj])

    t1 = Thread(target=predict_traj_direction, args=("left", x-25, y))
    t2 = Thread(target=predict_traj_direction, args=("right",x+15, y))
    t1.start()
    t1.join()
    t2.start()
    t2.join()

    #left
    #traj_left = predict_traj_direction("left", x-25, y)
    trajs = []
    trajs.append(q.get())
    trajs.append(q.get())
    for i in trajs:
        if i[0] == "left":
            traj_left = i[1]
        else:
            traj_right = i[1]
    #right
    # traj_right = predict_traj_direction("right", x+15, y)
    #check collisions
    oa = ObstacleAvoidance(mask)
    is_collide_left, boundRect = oa.check_collide_with_traj(traj_left)
    is_collide_right, _ = oa.check_collide_with_traj(traj_right, boundRect)

    is_collide = is_collide_left & is_collide_right
    traj = [traj_left, traj_right]

    return is_collide, traj, boundRect

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
    if objs is None or len(objs) == 0:
        return None
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


def start(server, botshell, autonomy=False, debug=False):
    if debug:
        rosimg = ros.ROSImage()
        rosimg.client.run()

    pd = PoseDetection()
    hd = HumanDetection()
    
    ht = HumanTracking(threshold=50)
    fd = FloorDetection()

    notifier = Notifier(botshell)
    htnm = Heteronomy((1024, 1280), botshell)
    atnm = Autonomy((1024, 1280), botshell)
    ctrl = atnm if autonomy else htnm
    ctrl.start()

    # Wait for autonomy process starting
    time.sleep(5)

    sm = StateMachine()
    
    cam_thread1 = CamThread("front_cam","/dev/video0",size_x=1024, size_y=1048)
    cam_thread2 = CamThread("down_cam", "/dev/video1")
    cam_thread1.start()
    cam_thread2.start()
    while True:
        #pilimg = camera.fetch(server)
        pilimg = cam_thread1.img
        down_cam_img = cam_thread2.img

        
        if pilimg is None:
            time.sleep(0.05)
            continue

        fpsstart = time.time()
        state = sm.get_state()
        print('Debug:', state)

        imgstart = time.time()
        img = np.asarray(pilimg)
        print("Size image: ", np.asarray(down_cam_img).shape)
        
        imgend = time.time()
        print('Image estimated time {:.4f}'.format(imgend-imgstart))

        # Stop
        if state == 'init_idle':
            notifier.say_waiting()
            notifier.send_status('idle')
            ctrl.rest()
            ht.reset()
            sm.next_state(True, 0.5)

        # Wait for an activation (raising hands)
        if state == 'idle':
            # Detect gesture
            ok = detect_gesture(pd, ht, img, 'activate')
            sm.next_state(ok, 0.5)

        # Run
        if state == 'init_run':
            notifier.say_ready()
            notifier.send_status('run')
            sm.next_state(True, 0.5)

        # Tracking
        if state == 'run':
            # Detect gesture
            # ok = detect_gesture(pd, ht, img, 'deactivate')
            ok = False
            # Detect human
            objs = detect_human(hd, img)
            # Handle state
            if ok:
                ctrl.wait()
                sm.next_state(True, 0.5)
            else:
                # Tracking
                box = tracking(ht, objs, img)
                if box is None:
                    ctrl.wait()
                    sm.next_state(True, 5)
                else:
                    print('tracking')
                    # Drive car
                    sm.next_state(False)

                    # Detect floor
                    t_seg = time.time()
                    mask = detect_floor(fd, down_cam_img)
                    print("time segment: ", time.time()-t_seg)

                    if not debug:
                        ctrl.goto(box)
                       
                        #get v_left, v_right to draw predicted trajectory of 2 wheels
                        v_left, v_right = ctrl.get_vlr(box)
                        print("Vleft: {}, Vright: {}".format(v_left, v_right))
                        x,y = mask.shape[1]//2 + 25, mask.shape[0]//2 - 10
                        theta = 0
                        
                        #mask = mask[0:mask.shape[0]//2, 0:mask.shape[1]//2]
                        limit_time = 0.3
                        t_stop = time.time()
                      
                        mask[np.where(mask == 0)] = 0
                        mask[np.where(mask == 1)] = 255
                        
                        is_stop, traj, boundRect = stop_motion(mask, -v_left, -v_right, x,y,theta, limit_time)
                        
                        print("Is stop: ", is_stop)
                        print("Time stop: ", time.time()-t_stop)
                        print("Stop the robot when detecting obstacles: ", is_stop)
                        mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

                        #visualize the results
                        colors=[(255, 0, 0), (255, 255, 0), (0, 255, 0)]
                        color = 0
                        for direction_traj in traj:
                            for ii in range(len(direction_traj)-1):
                                mask = cv2.line(mask, (int(direction_traj[ii][0]), int(direction_traj[ii][1])), (int(direction_traj[ii+1][0]), int(direction_traj[ii+1][1])), colors[color], 1)
                            color += 1

                        for r in boundRect:
                            mask = cv2.rectangle(mask, (r[0], r[1]), (r[0]+r[2], r[1]+r[3]), (0,255,0),1)

                        # combine mask and original down cam image
                        mask = cv2.resize(mask, (down_cam_img.shape[1], down_cam_img.shape[0]))
                        horizontal_concat = np.concatenate((down_cam_img, mask), axis=1)
                        encoded, buffer = cv2.imencode('.jpg', horizontal_concat)
                        jpg_as_text = base64.b64encode(buffer)
                        #stream to the laptop
                        footage_socket.send(jpg_as_text)

                        if is_stop: #Stop
                            ctrl.stop()
                        else:
                            ctrl.goto(box)
                    # Draw bounding box of tracking objective
                    if debug:
                        img = image.draw_box(img, box)

        # Publish ROS topic
        if debug:
            rosimg.apush(img)

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

