from time import sleep
from types import NoneType
import cv2
from cv2 import imwrite
import numpy as np
from out import out

from threadpool import threadpool
from square import Square

FONT = cv2.FONT_HERSHEY_SIMPLEX


class Image_Detection:
    def __init__(self, tl, tr, br, bl, start, minimum_change=0.9):
        self.tl = tl
        self.tr = tr
        self.br = br
        self.bl = bl

        self.minimum_change = minimum_change

        self.numbers = [str(i) for i in range(8*8)]
        self.box_poses = self.get_boxes(1024)

        values = []

        for x in range(8):
            row = []
            for y in range(8):
                row.append(str(7-x) + ", " + str(7 - y))
            values.append(row)

        self.prev = self.crop_board(tl, tr, br, bl, start, (1024, 1024))

        self.prev = cv2.flip(self.prev, 0)
        self.prev = cv2.flip(self.prev, 1)

        self.boxes = self.gen_boxes(self.prev)

        self.squares = np.zeros((8, 8), dtype=Square)
        for x in range(8):
            for y in range(8):
                self.squares[x][y] = Square(self.boxes[x][y])

        self.prev = cv2.flip(self.prev, 0)
        self.prev = cv2.flip(self.prev, 1)

    def gen_boxes(self, img):
        squares = np.zeros((8, 8), dtype=np.ndarray)
        for x in range(8):
            for y in range(8):
                box_pos = self.box_poses[x][y]
                squares[x][y] = img[box_pos[0][1]:box_pos[1]
                                    [1], box_pos[0][0]:box_pos[1][0]]
        return squares

    def crop_board(self, tl, tr, br, bl, image, size):
        rect = np.float32((tl, tr, br, bl))
        dst = np.float32(
            ((0, 0), (image.shape[0], 0), (image.shape[0], image.shape[1]), (0, image.shape[1])))

        # compute the perspective transform matrix and then apply it
        matrix = cv2.getPerspectiveTransform(
            rect, dst)
        warped = cv2.warpPerspective(
            image, matrix, (image.shape[0], image.shape[1]))

        # return the warped image
        return cv2.resize(warped, size)

    def draw_grid(self, img, values):
        for x in range(8):
            for y in range(8):
                box = self.box_poses[x][y]
                cv2.rectangle(img, box[0], box[1], (255, 255, 0), 3)
                if not isinstance(values, NoneType):
                    cv2.putText(img, values[x][y],
                                (box[0][0] + 6, box[1][1] - 10), FONT, 1, (255, 0, 255), 2)

        return img

    def get_boxes(self, w):
        boxes = np.zeros((8, 8), dtype=tuple)
        grid_size = int(w / 8)
        size = int(grid_size / 3)
        offset = int((grid_size - size) / 2)

        for x in range(8):
            for y in range(8):
                boxes[x][y] = ((x*grid_size + offset, y*grid_size + offset), (x*grid_size +
                                                                              size + offset, y*grid_size+size + offset), (size, size))

        return boxes

    def rollback(self):
        for x in range(8):
            for y in range(8):
                self.squares[x][y].prev = self.squares[x][y].rollback
                self.squares[x][y].rollback = None

    @threadpool
    def wait_until_moved(self, cap):
        self.waiting = True
        while self.waiting:
            stills = 0
            while True:
                cv2.waitKey(50)
                ret, frame = cap.read()
                sim = self.match_self(frame)
                if sim < 2:
                    stills += 1
                else:
                    stills = 0

                if stills >= 2:
                    break
            print("Matching..")
            a, b, sim = self.match(cap.read()[1])
            print("Matched..", sim)
            if sim < self.minimum_change:
                self.waiting = False
                return a, b
        print("wait_until_moved", "Exitted without returning...")

    def match_self(self, next):
        prev = self.prev.copy()

        next = self.crop_board(self.tl, self.tr, self.br,
                               self.bl, next, (1024, 1024))
        self.prev = next.copy()

        prev = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
        next = cv2.cvtColor(next, cv2.COLOR_BGR2GRAY)

        next = cv2.flip(next, 0)
        next = cv2.flip(next, 1)

        prev = cv2.flip(prev, 0)
        prev = cv2.flip(prev, 1)

        next = cv2.GaussianBlur(src=next, ksize=(5, 5), sigmaX=0)
        prev = cv2.GaussianBlur(src=prev, ksize=(5, 5), sigmaX=0)

        diff_frame = cv2.absdiff(src1=next, src2=prev)

        kernel = np.ones((5, 5))

        diff_frame = cv2.dilate(diff_frame, kernel, 1)

        thresh_frame = cv2.threshold(
            src=diff_frame, thresh=20, maxval=255, type=cv2.THRESH_BINARY)[1]

        average = thresh_frame.mean(axis=0).mean(axis=0)

        return average

    def match(self, next):
        next = self.crop_board(self.tl, self.tr, self.br,
                               self.bl, next, (1024, 1024))
        next = cv2.flip(next, 0)
        next = cv2.flip(next, 1)

        boxes = self.gen_boxes(next)
        values = []

        tasks = []

        for x in range(8):
            task_row = []
            for y in range(8):
                task_row.append(self.squares[x][y].match(boxes[x][y]))
            tasks.append(task_row)

        for x, row in enumerate(tasks):
            for y, task in enumerate(row):
                value = task.result()
                values.append({"value": value, "pos": (x, y)})

        values = sorted(values, key=lambda key: key["value"])

        next = cv2.flip(next, 0)
        next = cv2.flip(next, 1)

        self.prev = next

        self.draw_grid(next, None)

        return values[0]["pos"], values[1]["pos"], values[1]["value"]

    def calibrate(self, cap):
        ret, frame = cap.read()
        frame = self.crop_board(self.tl, self.tr, self.br,
                                self.bl, frame, (1024, 1024))
        boxes = self.gen_boxes(frame)
        test_square_1 = Square(boxes[0][7])
        test_square_2 = Square(boxes[0][0])
        out("Doe zet h8h6 en h1h3")
        input("Druk op enter wanneer je het hebt gedaan...")

        ret, frame = cap.read()
        frame = self.crop_board(self.tl, self.tr, self.br,
                                self.bl, frame, (1024, 1024))
        boxes = self.gen_boxes(frame)

        val_1 = test_square_1.match(boxes[0][7]).result()
        val_2 = test_square_2.match(boxes[0][0]).result()

        highest = val_1 if val_1 > val_2 else val_2

        self.minimum_change = highest + 0.07

        self.match(cap.read()[1])

        out("Herstel alles")
        input("Druk op enter wanneer je het hebt gedaan...")

        return self.minimum_change
