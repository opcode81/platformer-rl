import logging

from agent import *
from game import Game


log = logging.getLogger(__name__)


if __name__ == '__main__':
    logging.basicConfig()

    saveEveryNumTimeSteps = 250000

    game = Game("test2.grid", enableRendering=False)

    #agent = A2CAgent(game)
    agent = PPOAgent(game, load=True, suffix=750000)
    #agent = A2CAgent(load=True)

    while True:
        agent.train(saveEveryNumTimeSteps)
        log.info(f"Agent was trained for a total of {agent.totalTimeSteps} time steps")
        agent.save(suffix=f"{agent.totalTimeSteps}")
