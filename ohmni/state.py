from datetime import datetime
import numpy as np


class NoiseReduction:
    def __init__(self):
        self.start = None
        self.register = np.array([])
        self.threshold = 0.7

    def __reset(self):
        self.start = None
        self.register = np.array([])

    def __get_timestamp(self):
        return int(datetime.timestamp(datetime.now()))

    def input(self, bit, seconds):
        if self.start is None:
            print("Start ==================================")
            self.start = self.__get_timestamp()
        if self.__get_timestamp()-self.start < seconds:
            print("Bit", bit)
            self.register = np.append(self.register, bit)
            return None
        else:
            mean = np.mean(self.register)
            self.__reset()
            print("End ====================================", mean)
            return mean >= self.threshold


class StateMachine:
    def __init__(self):
        self.states = ['init_idle', 'idle', 'init_run', 'run']
        self.current_index = 0
        self.current_state = self.states[self.current_index]
        self.denoise = NoiseReduction()

    def __next(self):
        self.current_index = (self.current_index+1) % len(self.states)
        print("Next 1",  self.current_index)
        self.current_state = self.states[self.current_index]
        print("Next 2",  self.current_state)

    def __back(self):
        self.current_index = (self.current_index-1) % len(self.states)
        self.current_state = self.states[self.current_index]

    def __change_state(self, denoise_status):
        print('__change_state', denoise_status, denoise_status is True)
        if denoise_status is True:
            print("Vo ne ba")
            self.__next()
        else:  # No change
            pass

    def __throw_error(self):
        raise ValueError('The state is undefined.')

    def set_state(self, next_flag):
        if self.current_state == 'init_idle':
            print(1)
            self.__change_state(True)
        elif self.current_state == 'idle':
            ok = self.denoise.input(int(next_flag), 1)
            self.__change_state(ok)
            print(2, ok, self.current_state)
        elif self.current_state == 'init_run':
            print(3)
            self.__change_state(True)
        elif self.current_state == 'run':
            ok = self.denoise.input(int(next_flag), 20)
            self.__change_state(ok)
            print(4, ok, self.current_state)
        else:
            self.__throw_error()

    def get_state(self):
        return self.current_state
