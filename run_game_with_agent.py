import sys

from agent import PPOAgent
from game.game import Game

if __name__ == '__main__':
    argv = sys.argv[1:]
    if len(argv) == 0:
        levelFilename = None
    else:
        levelFilename = argv[0]

    game = Game(levelFilename=levelFilename)

    agent = PPOAgent(game, load=True)
    game.remoteController = agent.createRemoteController(deterministic=False)

    game.mainLoop()
