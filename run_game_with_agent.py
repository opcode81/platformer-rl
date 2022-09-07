import sys

from agent import PPOAgent
from game.game import Game

if __name__ == '__main__':
    levels = ["test.grid", "test2.grid", "test3.grid", "test4.grid"]
    game = Game(levels)

    agent = PPOAgent(game, load=True, suffix="4750000")
    game.remoteController = agent.createRemoteController(deterministic=False)

    game.mainLoop()
