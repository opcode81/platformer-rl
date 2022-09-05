from agent import *
from game import Game


log = logging.getLogger(__name__)


if __name__ == '__main__':
    logging.basicConfig()

    saveEveryNumTimeSteps = 250000
    enableRendering = True  # disable to increase learning speed (almost double)

    game = Game("test3.grid", enableRendering=enableRendering)

    #agent = A2CAgent(game)
    agent = PPOAgent(game, load=True, suffix=1500000)

    while True:
        agent.train(saveEveryNumTimeSteps)
        log.info(f"Agent was trained for a total of {agent.totalTimeSteps} time steps")
        agent.save(suffix=f"{agent.totalTimeSteps}")
