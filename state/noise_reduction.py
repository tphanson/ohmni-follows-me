from datetime import datetime
import numpy as np


class NoiseReduction:
    def __init__(self, threshold, duration):
        self.threshold = threshold
        self.duration = duration
        self.start = None
        self.register = np.array([])

    def reset(self):
        self.start = None
        self.register = np.array([])

    def __get_timestamp(self):
        return datetime.timestamp(datetime.now())

    def input(self, bit):
        # start is not set
        if self.start is None:
            self.start = self.__get_timestamp()
        # start is outdated
        if self.__get_timestamp()-self.start > 2*self.duration:
            self.start = self.__get_timestamp()

        if self.__get_timestamp()-self.start < self.duration:
            self.register = np.append(self.register, bit)
            return None
        else:
            mean = np.mean(self.register)
            self.reset()
            return 1 if mean >= self.threshold else 0
