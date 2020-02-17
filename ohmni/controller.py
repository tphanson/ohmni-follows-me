import numpy as np

# RO: 0.00253 rad/s/unit ; unit: (1,1)
# MOV: 0.43 mm/s/unit ; unit: (1,-1)

# Speed of rotation
SLOW_RO = 100
MEDIUM_RO = 200
FAST_RO = 350
# Speed of run
SLOW_MO = 700
MEDIUM_MO = 1000
FAST_MO = 1700
# Action zones
AREA = np.array([1/10, 1/6, 2/9, 1/3])
XMED = np.array([11/30, 13/30, 14/30, 16/30, 17/30, 19/30])


class Controller:
    def __init__(self, frame_shape):
        self.frame_shape = frame_shape
        self.xmed = XMED*self.frame_shape[0]
        self.area = AREA*self.frame_shape[0]*self.frame_shape[1]

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
            left_margin = self.xmed[1]
            right_margin = self.xmed[4]
            speed = MEDIUM_RO

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

    def wheel(self, area, xmed):
        lw_run, rw_run, run = self.run(area)
        lw_rotate, rw_rotate = self.rotate(xmed, run)
        left_wheel = 0
        right_wheel = 0
        left_wheel = left_wheel + lw_run + lw_rotate
        right_wheel = right_wheel + rw_run + rw_rotate
        return left_wheel, right_wheel

    def head(self, bbox):
        pass
