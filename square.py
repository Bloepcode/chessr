from types import NoneType
import cv2

from threadpool import threadpool


class Square:
    def __init__(self, start):
        self.prev = start
        self.rollback = None

        # def match(self, next, i):
        #     next = cv2.cvtColor(next, cv2.COLOR_BGR2GRAY)
        #     orb = cv2.ORB_create(edgeThreshold=20, patchSize=31, nlevels=8, fastThreshold=15,
        #                          scaleFactor=1.2, WTA_K=2, scoreType=cv2.ORB_HARRIS_SCORE, firstLevel=0, nfeatures=10000)

        #     kp1, des1 = orb.detectAndCompute(self.prev, None)
        #     kp2, des2 = orb.detectAndCompute(next, None)

        #     if isinstance(des1, NoneType) or isinstance(des2, NoneType):
        #         return 0

        #     bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

        #     matches = bf.match(des1, des2)

        #     img3 = cv2.drawMatches(self.prev, kp1, next, kp2,
        #                            matches[:50], None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

        #     cv2.imwrite(f"out/num-{i}.png", img3)

        #     self.prev = next

        #     return len(matches)
    def match(self, next):

        errorL2 = cv2.norm(self.prev, next, cv2.NORM_L2)

        sim = 1 - errorL2 / (128 * 128)
        self.rollback = self.prev
        self.prev = next
        return sim
