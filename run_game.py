import sys

from game.game import Game

if __name__ == '__main__':
    argv = sys.argv[1:]
    if len(argv) == 0:
        levels = ["test.grid", "test2.grid", "test3.grid", "test4.grid"]
    else:
        levels = [argv[0]]
    game = Game(levels)
    game.mainLoop()
    #game.mainLoopRemoteControlledTest()
