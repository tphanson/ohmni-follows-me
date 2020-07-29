import time
import numpy as np
import cv2 as cv
import queue
import threading
from detection import floornet

# RO: 0.00253 rad/s/unit ; unit: (1,1)
# MOV: 0.43 mm/s/unit ; unit: (1,-1)

# ALPHA = meter * pixel^2, pixel^2 = scaled box area
ALPHA = 0.2
# BETA = average human shoulder length (meter)
BETA = 0.4

# Ohmni global config
NECK_POS = 500

# Speed of rotation
ROTATION = 450
# Speed of run
BACKWARD = 600
FORWARD = 1900
# Speed of neck
NECK_DELTA = 10
NECK = [300, 550]
# Action zones
XSCALE = np.array([6/30, 9/30, 11/30])
YSCALE = np.array([4/7, 5/7])


class Estimation:
    def __init__(self, frame_shape):
        self.frame_shape = frame_shape
        self.xscale = XSCALE*self.frame_shape[1]
        self.yscale = YSCALE*self.frame_shape[0]
        self.neck_position = NECK_POS

    def calculate(self, bbox):
        [xmin, ymin, xmax, ymax] = bbox
        width = xmax - xmin
        height = ymax - ymin
        xmed = (xmin + xmax)/2
        ymed = (ymin + ymax)/2
        return width, height, xmed, ymed

    def rotate(self, xmed):
        # if urgency > 0: right, else: left
        urgency = (xmed/self.frame_shape[1] - 0.5)/0.5
        speed = int(ROTATION*urgency)
        print('*** Debug: (xmed, speed, urgency)', xmed, speed, urgency)
        return speed, speed, abs(urgency)

    def run(self, width):
        ratio = min(
            1, max(0, (self.xscale[1]-width)/(self.xscale[1] - self.xscale[0])))
        print('*** Debug: (width, ratio)', width, ratio)
        if width >= self.xscale[2]:  # Slow Backward
            return -BACKWARD, BACKWARD
        elif self.xscale[2] > width >= self.xscale[1]:  # Safe zone
            return 0, 0
        else:  # Fast Forward
            return FORWARD*ratio, -FORWARD*ratio

    def wheel(self, box):
        width, _, xmed, _ = self.calculate(box)
        lw_run, rw_run = self.run(width)
        lw_rotate, rw_rotate, urgency = self.rotate(xmed)
        lw = lw_run*(1-urgency) + lw_rotate
        rw = rw_run*(1-urgency) + rw_rotate
        return int(lw), int(rw)

    def neck(self, box):
        _, _, _, ymed = self.calculate(box)
        if ymed >= self.yscale[1]:
            self.neck_position -= NECK_DELTA
        elif self.yscale[1] > ymed >= self.yscale[0]:
            pass
        else:
            self.neck_position += NECK_DELTA

        return min(max(self.neck_position, NECK[0]), NECK[1])

    def pose(self, box):
        # Calculate x
        width, height, xmed, _ = self.calculate(box)
        area = width * height
        x = ALPHA/(area/(self.frame_shape[0]*self.frame_shape[1]))
        # Calculate y
        [xmin, _, xmax, _] = box
        y = (self.frame_shape[1]/2 - xmed)*BETA/(xmax - xmin)
        return x, y


class Autonomy:
    def __init__(self, frame_shape, botshell):
        self.frame_shape = frame_shape
        self.botshell = botshell
        self.estimation = Estimation(frame_shape)

    def start(self):
        print('*** Start autonomy move')
        self.botshell.sendall(b'start_autonomy\n')

    def stop(self):
        print('*** Stop autonomy move')
        self.botshell.sendall(b'stop_autonomy\n')

    def goto(self, box):
        # Estimate controller params
        x, y = self.estimation.pose(box)
        t = int(time.time()*1000)
        pos = self.estimation.neck(box)
        # Static test
        print('*** Autonomy move:', x, y, t)
        print('*** Neck position:', pos)
        # Dynamic test
        self.botshell.sendall(f'follow_me {x} {y} {t}\n'.encode())
        self.botshell.sendall(f'neck_angle {pos}\n'.encode())

    def wait(self):
        t = int(time.time()*1000)
        print('*** Autonomy move:', 0.7, 0, t)
        self.botshell.sendall(f'follow_me 0.7 0 {t}\n'.encode())

    def rest(self):
        t = int(time.time()*1000)
        print('*** Autonomy move:', 0, 0, t)
        print('*** Neck position:', NECK_POS)
        self.botshell.sendall(f'follow_me 0 0 {t}\n'.encode())
        self.botshell.sendall(f'neck_angle {NECK_POS}\n'.encode())


class Heteronomy:
    def __init__(self, frame_shape, botshell):
        self.frame_shape = frame_shape
        self.botshell = botshell
        self.estimation = Estimation(frame_shape)
        self.floorNet = floornet.FloorNet(frame_shape)
        self.camera = cv.VideoCapture(1)
        self.camera.set(3, 320)
        self.camera.set(4, 240)

        self.q = queue.Queue(maxsize=2)

    def start(self):
        """ Start the controller thread """
        print('*** Start manual move')
        t = threading.Thread(target=self._goto, args=(), daemon=True)
        t.start()

    def stop(self):
        """ Stop Ohmni, set neck to initial state """
        print('*** Stop manual move')
        self.botshell.sendall(b'manual_move 0 0\n')
        self.botshell.sendall(f'neck_angle {NECK_POS}\n'.encode())

    def _goto(self):
        """ Fetch data from queue and execute it """

        while True:
            # Get box
            box = self.q.get()
            print("==========", box)
            if box is None:
                time.sleep(0.05)  # Recheck in 20Hz
                continue

            # Estimate controller params
            lw, rw = self.estimation.wheel(box)
            pos = self.estimation.neck(box)
            _, img = self.camera.read()
            _, _, collision = self.floorNet.predict(img)
            if collision:
                print('*** Collision detected')
                self.wait()
            else:
                print('*** Manual move:', lw, rw)
                print('*** Neck position:', pos)
                self.botshell.sendall(f'manual_move {lw} {rw}\n'.encode())
                self.botshell.sendall(f'neck_angle {pos}\n'.encode())

    def goto(self, box):
        """ Feed data to queue for other processes using """
        if self.q.full():
            self.q.get(box) # Prevent block
        self.q.put(box)

    def wait(self):
        print('*** Manual move:', 0, 0)
        self.botshell.sendall(b'manual_move 0 0\n')

    def rest(self):
        print('*** Manual move:', 0, 0)
        print('*** Neck position:', NECK_POS)
        self.botshell.sendall(b'manual_move 0 0\n')
        self.botshell.sendall(f'neck_angle {NECK_POS}\n'.encode())


class Notifier:
    def __init__(self, botshell):
        self.botshell = botshell

    def say_ready(self):
        self.botshell.sendall(b'say I\'m ready\n')

    def say_waiting(self):
        self.botshell.sendall(b'say ok I\'m waiting for you\n')

    def send_status(self, status):
        self.botshell.sendall(f'broadcast_following_me {status}\n'.encode())
