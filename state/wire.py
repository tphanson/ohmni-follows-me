import threading
import time
from queue import Queue, Empty

from state.noise_reduction import NoiseReduction


class Wire:
    def __init__(self, signal, threshold=0.5, duration=1):
        self.signal = signal
        self.queue = Queue(1)
        self.denoise = NoiseReduction(threshold, duration)
        self.max_hz = 25
        self.level = 0
        self.signal_reader = threading.Thread(
            target=self.__signal_thread,
            args=(self.signal, self.max_hz, self.denoise, self.queue),
            daemon=True
        )
        self.__plug_signal()

    def __signal_thread(self, signal, max_hz, denoise, queue):
        def set_queue(queue, bit):
            if queue.full():
                queue.get()
            queue.put(bit)

        def restrict_freq(max_hz, start, end):
            delay = 1/max_hz - start + end
            if delay > 0:
                time.sleep(delay)

        while True:
            start = time.time()

            level = denoise.input(signal())
            if level is not None:
                set_queue(queue, level)

            end = time.time()
            restrict_freq(max_hz, start, end)

    def __plug_signal(self):
        if not self.signal_reader.isAlive():
            self.signal_reader.start()

    def get(self):
        try:
            self.level = self.queue.get_nowait()
        except Empty:
            pass
        return self.level
