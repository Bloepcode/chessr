from types import NoneType
import cv2

from threadpool import threadpool


class Square:
    def __init__(self, start):
        self.prev = start
        self.rollback = None

    @threadpool
    def match(self, next):

        errorL2 = cv2.norm(self.prev, next, cv2.NORM_L2)

        sim = 1 - errorL2 / (128 * 128)
        self.rollback = self.prev
        self.prev = next
        return sim
