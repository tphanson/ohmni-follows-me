from datetime import datetime
import numpy as np


class NoiseReduction:
    def __init__(self):
        self.start = None
        self.register = np.array([])
        self.threshold = 0.7

    def get_timestamp(self):
        return int(datetime.timestamp(datetime.now()))

    def input(self, bit, seconds):
        if self.start is None:
            self.start = self.get_timestamp()
        if self.get_timestamp()-self.start < seconds:
            self.register = np.append(self.register, bit)
            return None
        else:
            self.start = None
            if np.mean(self.register) >= self.threshold:
                return True
            else:
                return False


class StateMachine:
    def __init__(self):
        self.states = ['init_idle', 'idle', 'init_run', 'run']
        self.current_state = self.states[1]
        self.denoise = NoiseReduction()

    def run(self):
        if self.current_state == 'run':
            pass
        elif self.current_state == 'init_run':
            ok = self.denoise.input(1, 1)
            if ok is True:
                self.current_state = 'run'
            else:
                self.current_state = 'idle'
        else:
            self.current_state = 'init_run'

    def idle(self):
        if self.current_state == 'idle':
            pass
        elif self.current_state == 'init_idle':
            ok = self.denoise.input(1, 20)
            if ok is True:
                self.current_state = 'idle'
            else:
                self.current_state = 'run'
        else:
            self.current_state = 'init_idle'

    def get(self):
        return self.current_state
