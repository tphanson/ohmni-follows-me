import time
import numpy as np

# RO: 0.00253 rad/s/unit ; unit: (1,1)
# MOV: 0.43 mm/s/unit ; unit: (1,-1)

# ALPHA = meter * pixel^2, pixel^2 = scaled box area
ALPHA = 0.2
# BETA = average human shoulder length (meter)
BETA = 0.4

# Ohmni global config
NECK_POS = 500

# Speed of rotation
SLOW_RO = 200
MEDIUM_RO = 300
FAST_RO = 400
DANGEROUS_AREA = 0.5
# Speed of run
SLOW_MO = 600
MEDIUM_MO = 1000
FAST_MO = 1600
# Speed of neck
NECK_DELTA = 10
NECK = [300, 550]
# Action zones
XSCALE = np.array([6/30, 7/30, 8/30, 9/30])
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

    def rotate(self, xmed, run):
        # if delta > 0: right, else: left
        delta = (xmed - self.frame_shape[1]/2)/(self.frame_shape[1]/2)
        speed = 0
        responsive = abs(delta) < DANGEROUS_AREA
        if run == 'fast':
            speed = int(SLOW_RO*delta)
        if run == 'medium':
            speed = int(MEDIUM_RO*delta)
        else:
            speed = int(FAST_RO*delta)
        print('*** Debug: (xmed, speed)', xmed, speed)
        print('*** Debug: (delta, responsive)', delta, responsive)
        return speed, speed, responsive

    def run(self, width):
        print('*** Debug: (width)', width)
        if width >= self.xscale[3]:  # Slow Backward
            return -SLOW_MO, SLOW_MO, 'slow'
        elif self.xscale[3] > width >= self.xscale[2]:  # Safe zone
            return 0, 0, 'slow'
        elif self.xscale[2] > width >= self.xscale[1]:  # Slow Forward
            return SLOW_MO, -SLOW_MO, 'slow'
        elif self.xscale[1] > width >= self.xscale[0]:  # Medium Forward
            return MEDIUM_MO, -MEDIUM_MO, 'medium'
        else:  # Fast Forward
            return FAST_MO, -FAST_MO, 'fast'

    def wheel(self, box):
        width, _, xmed, _ = self.calculate(box)
        lw_run, rw_run, speed = self.run(width)
        lw_rotate, rw_rotate, responsive = self.rotate(xmed, speed)
        lw = 0
        rw = 0
        if responsive:
            lw = lw_run + lw_rotate
            rw = rw_run + rw_rotate
        else:
            lw = lw_rotate
            rw = rw_rotate
        return lw, rw

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

    def start(self):
        print('*** Start manual move')

    def stop(self):
        print('*** Stop manual move')
        self.botshell.sendall(b'manual_move 0 0\n')
        self.botshell.sendall(f'neck_angle {NECK_POS}\n'.encode())

    def goto(self, box):
        # Estimate controller params
        lw, rw = self.estimation.wheel(box)
        pos = self.estimation.neck(box)
        # Static test
        print('*** Manual move:', lw, rw)
        print('*** Neck position:', pos)
        # Dynamic test
        self.botshell.sendall(f'manual_move {lw} {rw}\n'.encode())
        self.botshell.sendall(f'neck_angle {pos}\n'.encode())

    def wait(self):
        print('*** Manual move:', 0, 0)
        self.botshell.sendall(b'manual_move 0 0\n')

    def rest(self):
        print('*** Manual move:', 0, 0)
        print('*** Neck position:', NECK_POS)
        self.botshell.sendall(b'manual_move 0 0\n')
        self.botshell.sendall(f'neck_angle {NECK_POS}\n'.encode())


class Say:
    def __init__(self, botshell):
        self.botshell = botshell

    def ready(self):
        self.botshell.sendall(b'say I\'m ready\n')

    def wait(self):
        self.botshell.sendall(b'say ok I\'m waiting for you\n')
