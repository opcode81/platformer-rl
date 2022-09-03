import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

import gym
import numpy as np
from stable_baselines3 import A2C, DQN, PPO
from stable_baselines3.common.base_class import BaseAlgorithm
import pygame

from game import Game
from game.debug import log
from game.level import GridLevel
from game.objects import ControlledAvatar
from game.remote_control import RemoteAction, RemoteActionEventGenerator, RemoteController

AGENT_STORAGE_PATH = os.path.join("models")


class Env(gym.Env):
    metadata = {"render_modes": ["ansi"], "render_fps": 4}

    GRID_CONTEXT = 5

    def __init__(self, game):
        self.rand = np.random.RandomState()
        self.game = game
        gridContextSize = (2 * self.GRID_CONTEXT + 1) * (2 * self.GRID_CONTEXT + 1)
        obsSize = 2 * gridContextSize
        obsSize += 2  # exit direction
        obsSize += 2  # avatar position offset in cell
        obsSize += 2 * 2  # avatar acceleration and velocity vectors
        obsSize += 3  # avatar motion flags
        self.observation_space = gym.spaces.Box(-1.0, 1.0, shape=[obsSize])
        self.actions = list(RemoteAction)
        self.action_space = gym.spaces.Discrete(len(self.actions))
        self.prevScore = self.game.score
        self.actionGen: Optional[RemoteActionEventGenerator] = None

    def reset(self):
        self.game.resetLevel()
        self.actionGen = RemoteActionEventGenerator()
        return self.get_obs()

    def get_obs(self):
        av: ControlledAvatar = self.game.avatar
        if not isinstance(self.game.level, GridLevel):
            raise ValueError(f"Only levels of type {GridLevel} are supported")
        level: GridLevel = self.game.level
        exit = level.exits.sprites()[0]
        grid = level.grid
        avatarCell = grid.gridCellForPos(av.pos)
        exitDirection = np.sign(exit.pos - av.pos)
        positionOffsetInCell = grid.offsetInCell(av.pos)
        motionScale = 25
        acc = av.motion.accelerationVector() / motionScale
        vel = av.motion.velocityVector() / motionScale
        motionFlags = np.array([av.motion.onLeftWall, av.motion.onRightWall, av.motion.onGround]).astype(float)
        surroundingGrid = grid.surroundingGrid(avatarCell, self.GRID_CONTEXT, self.GRID_CONTEXT, self.GRID_CONTEXT, self.GRID_CONTEXT)
        gridPlatform: np.ndarray = (surroundingGrid == "X").astype(float)
        gridExit: np.ndarray = (surroundingGrid == "E").astype(float)
        obs = np.concatenate([gridPlatform.flatten(), gridExit.flatten(), exitDirection, positionOffsetInCell, vel, acc, motionFlags])
        return obs

    def step(self, actionIdx: int):
        # apply action
        action = self.actions[actionIdx]
        events = self.actionGen.actionToEvents(action)
        for e in events:
            pygame.event.post(e)

        # advance game
        self.game.processDataStreams()
        self.game.update()
        self.game.draw()

        reward = self.game.score - self.prevScore
        self.prevScore = self.game.score
        done = self.game.gameOver
        if done:
            log(f"Episode ended with score={self.game.score}")
        info = {}
        return self.get_obs(), reward, done, info

    def render(self, mode="ansi"):
        pass


class AgentRemoteController(RemoteController):
    def __init__(self, agent: "DeepRLAgent", deterministic=True):
        super().__init__()
        self.agent = agent
        self.deterministic = deterministic

    def _chooseAction(self) -> RemoteAction:
        obs = self.agent.env.get_obs()
        actionIdx, _ = self.agent.model.predict(obs, deterministic=self.deterministic)
        return self.agent.env.actions[actionIdx]


class DeepRLAgent(ABC):
    def __init__(self, game: Game, load: bool, filebasename: str, useFallbackForForbiddenActions=False):
        """
        :param load: whether to load a previously stored model
        :param filebasename: the base filename for storage
        :param useFallbackForForbiddenActions: whether to use, in cases where the policy selects an inadmissible action,
            the policy's probabilistic outputs to select a fallback action (the most probable admissible action).
            This option is useful for agents that have not been trained a lot; it will allow them to achieve better
            performance.
        """
        super().__init__()
        self.useFallbackForForbiddenActions = useFallbackForForbiddenActions
        self.env = Env(game)
        os.makedirs(AGENT_STORAGE_PATH, exist_ok=True)
        self.path = os.path.join(AGENT_STORAGE_PATH, f"{filebasename}.zip")
        self.model = self._createModel(self.env)
        if load:
            self.model = self.model.load(self.path)

    @abstractmethod
    def _createModel(self, env: Env) -> BaseAlgorithm:
        pass

    def train(self, total_timesteps):
        self.model.learn(total_timesteps=total_timesteps)

    def save(self):
        self.model.save(self.path)

    def createRemoteController(self, deterministic=True) -> AgentRemoteController:
        return AgentRemoteController(self, deterministic=deterministic)


class A2CAgent(DeepRLAgent):
    def __init__(self, game, load=False, useFallbackForForbiddenActions=False):
        super().__init__(game, load, "a2c", useFallbackForForbiddenActions=useFallbackForForbiddenActions)

    def _createModel(self, env) -> BaseAlgorithm:
        return A2C('MlpPolicy', env, verbose=1)


class DQNAgent(DeepRLAgent):
    def __init__(self, game, load=False):
        super().__init__(game, load, "dqn")

    def _createModel(self, env) -> BaseAlgorithm:
        return DQN('MlpPolicy', env, verbose=1)


class PPOAgent(DeepRLAgent):
    def __init__(self, game, load=False):
        super().__init__(game, load, "ppo")

    def _createModel(self, env) -> BaseAlgorithm:
        return PPO('MlpPolicy', env, verbose=1)



