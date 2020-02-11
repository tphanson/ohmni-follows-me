# RO: 0.00253 rad/s/unit ; unit: (1,1)
# MOV: 0.43 mm/s/unit ; unit: (1,-1)

# Speed of rotation
SLOW_RO = 100
MEDIUM_RO = 200
FAST_RO = 350
# Speed of run
SLOW_MO = 500
MEDIUM_MO = 1000
FAST_MO = 2500
# Action zones
AREA = [8000, 15000, 20000, 30000]
XMED = [115, 140, 160, 185]


class Controller:
    def __init__(self):
        pass

    def rotate(self, xmed, run):
        left_margin = 0
        right_margin = 0
        speed = 0
        if run == 'fast':
            left_margin = XMED[1]
            right_margin = XMED[2]
            speed = SLOW_RO
        elif run == 'medium':
            left_margin = XMED[1]
            right_margin = XMED[2]
            speed = MEDIUM_RO
        elif run == 'slow':
            left_margin = XMED[0]
            right_margin = XMED[3]
            speed = FAST_RO
        else:
            left_margin = XMED[0]
            right_margin = XMED[3]
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

        if area >= AREA[3]:
            # Medium Backward
            run = 'medium'
            left_wheel = left_wheel - MEDIUM_MO
            right_wheel = right_wheel + MEDIUM_MO
        elif AREA[3] > area >= AREA[2]:
            # Safe zone
            run = 'safe'
            left_wheel = 0
            right_wheel = 0
        elif AREA[2] > area >= AREA[1]:
            # Slow Forward
            run = 'slow'
            left_wheel = left_wheel + SLOW_MO
            right_wheel = right_wheel - SLOW_MO
        elif AREA[1] > area >= AREA[0]:
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

    def calculate(self, area, xmed):
        lw_run, rw_run, run = self.run(area)
        lw_rotate, rw_rotate = self.rotate(xmed, run)
        left_wheel = 0
        right_wheel = 0
        left_wheel = left_wheel + lw_run + lw_rotate
        right_wheel = right_wheel + rw_run + rw_rotate
        return left_wheel, right_wheel
