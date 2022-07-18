import re
from threading import Thread
import json
import chess
import chess.svg
import cv2
from image_detection import Image_Detection
from time import sleep
from stockfish import Stockfish
from stockfish.models import StockfishException
from threadpool import cancel_task, threadpool

from out import out


FONT = cv2.FONT_HERSHEY_SIMPLEX

NUM_TO_LETTER = {
    0: 'a',
    1: 'b',
    2: 'c',
    3: 'd',
    4: 'e',
    5: 'f',
    6: 'g',
    7: 'h'
}


class Chessr():
    def __init__(self, codes, board, skill, cam, fen):
        self.gui = None
        # Init board
        self.board = chess.Board()

        if fen:
            self.board.set_fen(fen)

        # Set board if nessecary else reset
        if board:
            with open(board, "r") as f:
                # self.board.set_fen(f.read())
                for action in f.read().split("\n"):
                    if action == "":
                        continue
                    self.board.push_uci(action)
        else:
            with open("board.txt", "w") as f:
                f.write("")

        # Get camera
        self.cap = cv2.VideoCapture(cam)
        sleep(0.3)
        ret, self.frame = self.cap.read()

        # Get chessboard points
        minimum_change = 0
        points = []

        if not codes:
            self.clicked = False
            self.mouseX = 0
            self.mouseY = 0
            points = self.get_points()
        else:
            with open(codes, "r") as f:
                codes = json.load(f)
                for i in range(4):
                    points.append(
                        (codes["coords"][i][0], codes["coords"][i][1]))
                minimum_change = codes["minimum_change"]

        # Init im_de
        self.im_de = Image_Detection(points[0], points[1],
                                     points[2], points[3], self.frame)

        # Calibrate if nessecary
        if not codes:
            out("Bezig met kalibreren")
            minimum_change = self.im_de.calibrate(self.cap)
            with open("out_codes.json", "w") as f:
                json.dump({
                    "coords": points,
                    "minimum_change": minimum_change
                }, f)

        # Warn with bad calibration
        # if minimum_change >= 0.8:
            # out("Het licht en schaakbord zijn niet heel goed waardoor er meer fouten dan normaal kunnen worden gemaakt...")

        # Set minimum change
        self.im_de.minimum_change = minimum_change

        # Init stockfish
        self.stockfish = Stockfish(
            "/opt/homebrew/Cellar/stockfish/15/bin/stockfish", parameters={"Skill Level": skill})
        self.stockfish.set_fen_position(self, self.board.fen())

        # Start loop
        self.mainloop_task = self.mainloop()

    def write_board(self, board, move=None):
        if move:
            svg = chess.svg.board(board, lastmove=chess.Move.from_uci(move))
        else:
            svg = chess.svg.board(board)

        with open("out.svg", "w") as f:
            f.write(svg)
        self.gui.set_board()

    def write_action(self, action):
        with open("board.txt", "a") as f:
            f.write(action + "\n")

    def remove_actions(self):
        with open("board.txt", "r") as f:
            lines = f.read()
        with open("board.txt", "w") as f:
            print(lines)
            lines = lines.split("\n")[:-3]
            final = ""
            for line in lines:
                print("Remove", line)
                final += line + "\n"
            f.write(final)

    def get_points(self):
        out("Klik op de 4 punten van het schaakbord", wait=False)
        points = []
        cv2.namedWindow("Chess select")
        cv2.imshow("Chess select", self.frame)
        cv2.setMouseCallback('Chess select', self.click)
        for i in range(4):
            while not self.clicked:
                cv2.waitKey(20)
            self.clicked = False
            cv2.rectangle(self.frame, (self.mouseX, self.mouseY),
                          (self.mouseX, self.mouseY), (235, 183, 89), 10)
            cv2.imshow("Chess select", self.frame)
            print(self.mouseX, self.mouseY)
            points.append((self.mouseX, self.mouseY))
        cv2.destroyWindow("Chess select")
        return points

    def click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.clicked = True
            self.mouseX, self.mouseY = x, y

    def parse_poses_white(self, a, b):
        if self.board.color_at(chess.parse_square(f"{NUM_TO_LETTER[a[0]]}{7-a[1]+1}")) == chess.WHITE:
            return f"{NUM_TO_LETTER[a[0]]}{7-a[1]+1}{NUM_TO_LETTER[b[0]]}{7-b[1]+1}"
        else:
            return f"{NUM_TO_LETTER[b[0]]}{7-b[1]+1}{NUM_TO_LETTER[a[0]]}{7-a[1]+1}"

    def parse_poses_black(self, a, b):
        if self.board.color_at(chess.parse_square(f"{NUM_TO_LETTER[a[0]]}{7-a[1]+1}")) == chess.BLACK:
            return f"{NUM_TO_LETTER[b[0]]}{7-b[1]+1}{NUM_TO_LETTER[a[0]]}{7-a[1]+1}"
        else:
            return f"{NUM_TO_LETTER[a[0]]}{7-a[1]+1}{NUM_TO_LETTER[b[0]]}{7-b[1]+1}"

    def parse_poses(self, a, b):
        if self.turn == chess.BLACK:
            return self.parse_poses_black(a, b)
        else:
            return self.parse_poses_white(a, b)

    def wait_for_moved(self, title):
        # try:
        im_de_task = self.im_de.wait_until_moved(self.cap)
        gui_task = self.popup_options(title, ["Annuleer"])
        first, result = self.finished_first(im_de_task, gui_task)
        self.gui.remove_popups()
        if first == 0:
            return self.parse_poses(result[0], result[1])
        else:
            self.im_de.waiting = False
            return None

        # except KeyboardInterrupt:
        #     print("Overgeslagen")
        #     return None

    def popup_options_callback(self, sender, app_data, user_data):
        self.user_data = user_data

    @threadpool
    def popup_options(self, title, options):
        self.user_data = None
        self.gui.popup_options(title, options, self.popup_options_callback)

        while True:
            if self.user_data != None:
                self.gui.remove_popups()
                break
        return self.user_data

    def popup_string_callback(self, data):
        self.data = data

    @threadpool
    def popup_string(self, prompt):
        self.data = None
        self.gui.popup_string(prompt, self.popup_string_callback)

        while True:
            if self.data != None:
                self.gui.remove_popups()
                return self.data

    def finished_first(self, task1, task2):
        while True:
            if task1.done():
                cancel_task(task2)
                return 0, task1.result()
            elif task2.done():
                cancel_task(task1)
                return 1, task2.result()

    def get_move(self):
        # Try to auto-detect move
        # try:
        gui_task = self.popup_options(
            "Jouw beurt", ["Opties"])
        im_de_task = self.im_de.wait_until_moved(self.cap)
        result = self.finished_first(im_de_task, gui_task)
        self.gui.remove_popups()

        if result[0] == 1:
            self.im_de.waiting = False
            result = self.popup_options(
                "Opties", ["Herstart", "Undo", "Handmatig"]).result()
            if result == "Herstart":
                self.im_de.match(self.cap.read()[1])
                return None
            elif result == "Undo":
                # Pop ai and player move
                self.board.pop()
                self.board.pop()

                self.remove_actions()

                # Update stockfish
                self.stockfish.set_fen_position(self.board.fen)

                # Update output
                self.write_board(self.board)

                # Wait until player moved pieces
                self.popup_options("Zet de stukken terug", ["Oke"]).result()

                # Update im_de
                self.im_de.match(self.cap.read()[1])

                return None
            elif result == "Handmatig":
                return self.popup_string("Zet:").result()
        else:
            return self.parse_poses(result[1][0], result[1][1])

    def move_stockfish(self, move):
        try:
            self.stockfish.make_moves_from_current_position([
                move])
        except StockfishException:
            self.stockfish = Stockfish(
                "/opt/homebrew/Cellar/stockfish/15/bin/stockfish")
            self.stockfish.set_fen_position(self, self.board.fen())

    def try_move(self, move):
        try:
            self.board.push_uci(move)
        except ValueError:
            return False
        return True

    @threadpool
    def do_ai_move(self):
        while True:
            try:
                move = self.stockfish.get_best_move()
                self.board.push_uci(move)
                self.stockfish.make_moves_from_current_position([move])
                return move
            except StockfishException:
                self.stockfish = Stockfish(
                    "/opt/homebrew/Cellar/stockfish/15/bin/stockfish")
                self.stockfish.set_fen_position(self.board.fen())

    def check_move(self, move):
        while True:
            p_move = self.wait_for_moved("Doe de zet voor chessr")
            print(p_move, move)
            if move == p_move or p_move == None:
                return
            out("Zet het stukje terug", wait=False)
            self.wait_for_moved("Zet het stukje terug")
            out("Oke")
            self.im_de.match(self.cap.read()[1])
            out("Probeer het opnieuw", wait=False)

    @threadpool
    def mainloop(self):
        sleep(0.5)
        self.gui.set_turn(self.board.turn)
        self.write_board(self.board)
        out("Welkom bij chessr singleplayer!")
        try:
            while True:
                self.write_board(self.board)
                self.gui.set_turn(self.board.turn)
                self.turn = self.board.turn

                # Detect if it's our turn
                if self.board.turn == chess.WHITE:
                    out("\n\nJij bent aan de beurt", wait=False)
                    # get move
                    move = self.get_move()
                    if not move:
                        continue
                    # Try the move
                    if self.try_move(move):
                        self.write_action(move)

                        # Move stockfish ai
                        self.move_stockfish(move)
                        # Write to svg
                        self.write_board(self.board, move=move)
                        out(f"{move} is gelukt!")
                    else:
                        # Invalid move
                        try:
                            out(f"{move} mag niet")
                            out("Zet het stukje terug", wait=False)
                            # Wait until piece has put back
                            self.wait_for_moved("Zet het stukje terug")
                        except KeyboardInterrupt:
                            print("Geanuleerd")
                else:
                    ai_task = self.do_ai_move()
                    out("\n\nChessr is aan de beurt")
                    move = ai_task.result()
                    self.write_action(move)
                    self.write_board(self.board, move=move)
                    out(f"Ik kies {move}", wait=False)
                    print("Kan je dit voor mij zetten?")
                    self.check_move(move)
                if self.board.is_game_over():
                    out("Game over")
                    self.popup_options("Game over...", ["Exit"]).result()
                    return
        except KeyboardInterrupt:
            return
