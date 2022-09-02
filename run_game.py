import os
import sys

from game.game import Game

if __name__ == '__main__':
    argv = sys.argv[1:]
    if len(argv) == 0:
        levelFilename = None
    else:
        levelFilename = argv[0]
    if not os.path.exists("assets"): os.chdir("")
    game = Game(levelFilename=levelFilename)
    game.mainLoop()
    #game.mainLoopRemoteControlledTest()
