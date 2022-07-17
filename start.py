import argparse

import chess
from chessr import Chessr
from gui import Gui
from threadpool import cancel_task


parser = argparse.ArgumentParser(
    "Chessr", "Do some image processing with chessboards!")

parser.add_argument(
    "-c", "--codes", help="Chess codes including calibration", default=None)
parser.add_argument(
    "-b", "--board", help="Select the start board", default=None)
parser.add_argument("-s", "--skill", help="Skill level for AI", default=5)
parser.add_argument("-a", "--cam", help="the camera ID", default=2)

args = parser.parse_args()

chessr = Chessr(args.codes, args.board, args.skill, args.cam)

print("Chessr is geinitialiseerd!\n\n\n")

gui = Gui()

chessr.gui = gui

while True:
    if chessr.mainloop_task.done():
        chessr.mainloop_task.result()
        gui.stop()
    running = gui.update()
    if not running:
        break

cancel_task(chessr.mainloop_task).result()
