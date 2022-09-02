from agent import *
from game import Game

if __name__ == '__main__':
    logging.basicConfig()

    game = Game("test.grid")

    #agent = A2CAgent(game)
    agent = PPOAgent(game)
    #agent = A2CAgent(load=True)

    agent.train(3000000)
    agent.save()
