from agent import *
from game import Game


log = logging.getLogger(__name__)


def createGame():
    return Game("holes.grid", enableRendering=True)


class EnvWrapper(Env):
    def __init__(self, cfg):
        super().__init__(createGame())


if __name__ == '__main__':
    logging.basicConfig()

    saveEveryNumTimeSteps = 250000
    enableRendering = True  # disable to increase learning speed (almost double)

    #agent = A2CAgent(game)
    #agent = PPOAgent(game, load=False, suffix=4750000)
    agent = SACAgent(EnvWrapper, load=True, pathElems=["checkpoint_000501", "checkpoint-501"])

    while True:
        agent.train(saveEveryNumTimeSteps)
        log.info(f"Agent was trained for a total of {agent.totalTimeSteps} time steps")
        #agent.save(suffix=f"{agent.totalTimeSteps}")
