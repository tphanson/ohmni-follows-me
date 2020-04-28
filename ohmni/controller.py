import numpy as np

# RO: 0.00253 rad/s/unit ; unit: (1,1)
# MOV: 0.43 mm/s/unit ; unit: (1,-1)

# ALPHA = meter * pixel^2, pixel^2 = scaled box area
ALPHA = 0.15
# BETA = average human shoulder length (meter)
BETA = 0.4

# Ohmni global config
NECK_POS = 500

# Speed of rotation
SLOW_RO = 100
MEDIUM_RO = 200
FAST_RO = 400
# Speed of run
SLOW_MO = 700
MEDIUM_MO = 1100
FAST_MO = 1700
# Speed of neck
NECK_DELTA = 10
NECK = [300, 550]
# Action zones
AREA = np.array([3/30, 5/30, 7/30, 10/30])
XMED = np.array([11/30, 13/30, 14/30, 16/30, 17/30, 19/30])
YMED = np.array([4/7, 5/7])


class Estimation:
    def __init__(self, frame_shape):
        self.frame_shape = frame_shape
        self.area = AREA*self.frame_shape[0]*self.frame_shape[1]
        self.xmed = XMED*self.frame_shape[1]
        self.ymed = YMED*self.frame_shape[0]
        self.neck_position = NECK_POS

    def calculate(self, bbox):
        [xmin, ymin, xmax, ymax] = bbox
        area = (xmax-xmin) * (ymax-ymin)
        xmed = (xmin + xmax)/2
        ymed = (ymin + ymax)/2
        return area, xmed, ymed

    def rotate(self, xmed, run):
        left_margin = 0
        right_margin = 0
        speed = 0
        if run == 'fast':
            left_margin = self.xmed[2]
            right_margin = self.xmed[3]
            speed = SLOW_RO
        elif run == 'medium':
            left_margin = self.xmed[1]
            right_margin = self.xmed[4]
            speed = MEDIUM_RO
        elif run == 'slow':
            left_margin = self.xmed[0]
            right_margin = self.xmed[5]
            speed = FAST_RO
        else:
            left_margin = self.xmed[0]
            right_margin = self.xmed[5]
            speed = FAST_RO

        left_wheel = 0
        right_wheel = 0
        # Right
        if xmed >= right_margin:
            left_wheel = left_wheel + speed
            right_wheel = right_wheel + speed
        # Safe zone
        elif right_margin > xmed > left_margin:
            left_wheel = 0
            right_wheel = 0
        # Left
        else:
            left_wheel = left_wheel - speed
            right_wheel = right_wheel - speed

        return left_wheel, right_wheel

    def run(self, area):
        run = 'safe'
        left_wheel = 0
        right_wheel = 0

        if area >= self.area[3]:
            # Medium Backward
            run = 'medium'
            left_wheel = left_wheel - MEDIUM_MO
            right_wheel = right_wheel + MEDIUM_MO
        elif self.area[3] > area >= self.area[2]:
            # Safe zone
            run = 'safe'
            left_wheel = 0
            right_wheel = 0
        elif self.area[2] > area >= self.area[1]:
            # Slow Forward
            run = 'slow'
            left_wheel = left_wheel + SLOW_MO
            right_wheel = right_wheel - SLOW_MO
        elif self.area[1] > area >= self.area[0]:
            # Medium Forward
            run = 'medium'
            left_wheel = left_wheel + MEDIUM_MO
            right_wheel = right_wheel - MEDIUM_MO
        else:
            # Fast Forward
            run = 'fast'
            left_wheel = left_wheel + FAST_MO
            right_wheel = right_wheel - FAST_MO

        return left_wheel, right_wheel, run

    def wheel(self, box):
        area, xmed, _ = self.calculate(box)
        lw_run, rw_run, run = self.run(area)
        lw_rotate, rw_rotate = self.rotate(xmed, run)
        left_wheel = 0
        right_wheel = 0
        left_wheel = left_wheel + lw_run + lw_rotate
        right_wheel = right_wheel + rw_run + rw_rotate
        return left_wheel, right_wheel

    def neck(self, box):
        _, _, ymed = self.calculate(box)
        if ymed >= self.ymed[1]:
            self.neck_position -= NECK_DELTA
        elif self.ymed[1] > ymed >= self.ymed[0]:
            pass
        else:
            self.neck_position += NECK_DELTA

        if self.neck_position > NECK[1]:
            self.neck_position = NECK[1]
        if self.neck_position < NECK[0]:
            self.neck_position = NECK[0]
        return self.neck_position

    def pose(self, box):
        # Calculate x
        area, xmed, _ = self.calculate(box)
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
        pos = self.estimation.neck(box)
        # Static test
        print('*** Autonomy move:', x, y)
        print('*** Neck position:', pos)
        # Dynamic test
        self.botshell.sendall(f'follow_me {x} {y}\n'.encode())
        self.botshell.sendall(f'neck_angle {pos}\n'.encode())

    def wait(self):
        print('*** Autonomy move:', 1.01, 0)
        self.botshell.sendall(b'follow_me 1.01 0\n')

    def rest(self):
        print('*** Autonomy move:', 1.01, 0)
        print('*** Neck position:', NECK_POS)
        self.botshell.sendall(b'follow_me 1.01 0\n')
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
