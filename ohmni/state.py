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
        self.current_index = 1
        self.current_state = self.states[self.current_index]
        self.denoise = NoiseReduction()

    def __next(self):
        self.current_index = (self.current_index+1) % len(self.states)

    def __back(self):
        self.current_index = (self.current_index-1) % len(self.states)

    def __change_state(self, denoise_status):
        if denoise_status is True:
            self.__next()
        elif denoise_status is False:
            self.__back()
        else:
            # No change
            pass

    def run(self):
        if self.current_state == 'run':
            pass
        elif self.current_state == 'init_run':
            self.__change_state(None)
        else:
            ok = self.denoise.input(1, 1)
            print('run', ok)
            self.__change_state(ok)

    def idle(self):
        if self.current_state == 'idle':
            pass
        elif self.current_state == 'init_idle':
            self.__change_state(None)
        else:
            ok = self.denoise.input(1, 20)
            self.__change_state(ok)

    def get(self):
        return self.current_state
