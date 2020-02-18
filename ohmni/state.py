from datetime import datetime
import numpy as np


class NoiseReduction:
    def __init__(self):
        self.start = None
        self.register = np.array([])

    def __reset(self):
        self.start = None
        self.register = np.array([])

    def __get_timestamp(self):
        return int(datetime.timestamp(datetime.now()))

    def input(self, bit, seconds):
        if self.start is None:
            self.start = self.__get_timestamp()
        if self.__get_timestamp()-self.start < seconds:
            self.register = np.append(self.register, bit)
            return 0
        else:
            mean = np.mean(self.register)
            self.__reset()
            return mean


class StateMachine:
    def __init__(self):
        self.states = ['init_idle', 'idle', 'init_run', 'run']
        self.current_index = 0
        self.current_state = self.states[self.current_index]
        self.denoise = NoiseReduction()

    def __next(self):
        self.current_index = (self.current_index+1) % len(self.states)
        self.current_state = self.states[self.current_index]

    def __back(self):
        self.current_index = (self.current_index-1) % len(self.states)
        self.current_state = self.states[self.current_index]

    def __change_state(self, denoise_status):
        if denoise_status:
            self.__next()
        else:  # No change
            pass

    def __throw_error(self):
        raise ValueError('The state is undefined.')

    def next_state(self, next_flag):
        if self.current_state == 'init_idle':
            self.__change_state(True)
        elif self.current_state == 'idle':
            mean = self.denoise.input(int(next_flag), 1)
            self.__change_state(bool(mean >= 0.4))
        elif self.current_state == 'init_run':
            self.__change_state(True)
        elif self.current_state == 'run':
            mean = self.denoise.input(int(next_flag), 20)
            self.__change_state(bool(mean == 0))
        else:
            self.__throw_error()

    def get_state(self):
        return self.current_state
