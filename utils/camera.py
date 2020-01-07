import cv2 as cv
import threading
import time
from queue import Queue


class Camera:
    def __init__(self):
        self.queue = Queue(2)
        self.stop = threading.Event()
        self.stream_thread = threading.Thread(
            target=self.stream, args=(self.stop, self.queue, cv.VideoCapture(0),))
        self.play_thread = threading.Thread(
            target=self.play, args=(self.stop, self.queue, 1/24,))

    def play(self, stop, q, sec):
        print("You can press Q button to stop the test!")
        while True and not stop.wait(0.01):
            time.sleep(sec)
            frame = q.get()
            cv.imshow("camera-tups", frame)
            if cv.waitKey(10) & 0xFF == ord('q'):
                break
        cv.destroyWindow("camera-tups")

    def stream(self, stop, q, stream):
        while stream.isOpened() and not stop.wait(0.01):
            ret, frame = stream.read()
            if ret is not True:
                break
            if q.full():
                q.get()
            q.put(frame)

    def test_camera(self):
        if not self.stream_thread.isAlive():
            self.stream_thread.start()
        if not self.play_thread.isAlive():
            self.play_thread.start()

    def get_stream(self):
        if not self.stream_thread.isAlive():
            self.stream_thread.start()
        return self.queue

    def terminate(self):
        self.stop.set()
        if self.play_thread.isAlive():
            self.play_thread.join()
        if self.stream_thread.isAlive():
            self.stream_thread.join()
