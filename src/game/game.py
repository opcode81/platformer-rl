import os
import sys
from typing import Optional

import numpy as np
import pygame
from pygame import sprite
from pygame.locals import K_ESCAPE

from . import config
from .camera import ChasingCamera
from .debug import log
from .events import EventHandler
from .level import Level, loadLevel, GridLevel
from .objects import ControlledAvatar, Ghost
from .remote_control import RemoteActionEventGenerator, RemoteAction, RemoteController
from .renderer import GameRenderer


class Game(EventHandler):
    width = 800
    height = 600
    FRAME_RATE = 60
    SCORE_EXIT = 100
    SCORE_PER_SECOND = -1
    SCORE_TICK = SCORE_PER_SECOND/FRAME_RATE
    SCORE_DEATH = -1000
    SCORE_EXIT_CLOSENESS_PER_STEP = 10
    EXIT_CLOSENESS_STEP_SIZE = 40

    def __init__(self, levelFilename=None, enableRendering=True):
        log(f"Initialising game (level={levelFilename})")
        EventHandler.__init__(self, self)
        
        pygame.init()
        self.enableRendering = enableRendering
        self.renderer = None
        self.level: Optional[Level] = None
        self.timer = pygame.time.Clock()
        self.screen = pygame.display.set_mode((Game.width, Game.height))
        self.running = True
        self.gameOver = False
        self.remoteController: Optional[RemoteController] = None
        pygame.display.set_caption("Tempus Temporis [prototype]")
        self.width, self.height = self.screen.get_size()

        # only for logging purposes
        self.maxAbsVel = np.array([0,0])
        self.maxAbsAcc = np.array([0,0])

        path = config.levelsPath
        self.states = set()

        files = os.listdir(path)
        files.sort()

        level = None
        for inFile in files:
            if inFile == levelFilename:
                level = loadLevel(os.path.join(path, inFile), self)

        if level is None:
            print(f"No level selected; the following filenames were found: {files}")
            sys.exit(1)

        self.startLevel(level)

    def update(self):
        # advance time
        self.time += 1
        self.score += self.SCORE_TICK

        exitDistanceSteps = self.existDistanceSteps()
        if exitDistanceSteps < self.bestExitDistanceSteps:
            stepsCloser = self.bestExitDistanceSteps - exitDistanceSteps
            self.score += self.SCORE_EXIT_CLOSENESS_PER_STEP * stepsCloser
            self.bestExitDistanceSteps = exitDistanceSteps

        self.camera.update(self)
        self.renderer.update(self)

        #self._logState()

    def draw(self):
        if self.enableRendering:
            self.renderer.draw()

    def _logState(self):
        vel = self.avatar.motion.velocityVector()
        acc = self.avatar.motion.accelerationVector()
        self.maxAbsVel = np.maximum(np.abs(vel), self.maxAbsVel)
        self.maxAbsAcc = np.maximum(np.abs(acc), self.maxAbsAcc)
        log(f"vel={vel}, acc={acc}, max(abs(vel))={self.maxAbsVel}, max(abs(acc))={self.maxAbsAcc}")
        if isinstance(self.level, GridLevel):
            level = self.level
            cell = level.grid.gridCellForPos(self.avatar.pos)
            log(f"Grid cell: {cell}")
            log(f"Offset on cell: {level.grid.offsetInCell(self.avatar.pos)}")
            log(f"Surroundings:\n{self.level.grid.surroundingGrid(cell, 5, 5, 5, 5)}")

    def createAvatars(self):        
        self.avatar = ControlledAvatar(self.level.playerInitialPos, self)
        self.avatars = sprite.Group(self.avatar)

    def startLevel(self, level):
        log("starting level")
        self.eventHandlers = []        

        self.level = level
        self.level.reset()

        self.createAvatars()

        self.renderer = GameRenderer(self)
        self.renderer.add(self.level)
        self.renderer.add(self.avatars)

        self.gameOver = False
        self.score = 0
        self.time = 0
        self.bestExitDistanceSteps = self.existDistanceSteps()
        
        self.camera = ChasingCamera(self)

        if self.remoteController is not None:
            self.remoteController.reset()

    def existDistanceSteps(self):
        offs = self.avatar.pos - self.level.exits.sprites()[0].pos
        dist = np.linalg.norm(offs)
        return dist / self.EXIT_CLOSENESS_STEP_SIZE
    
    def travelBackInTime(self):
        # add ghost
        ghost = Ghost(self.avatar)
        self.renderer.add(ghost)        
        
        # replace avatar
        self.avatar.kill()        
        self.avatar = ControlledAvatar(self.level.playerInitialPos, self)
        self.avatars.add(self.avatar)
        self.renderer.add(self.avatar) # TODO should this be necessary?
        
        self.time = 0

    def playerDies(self):
        log("player has died")
        self.score += self.SCORE_DEATH
        self.gameOver = True

    def playerExitsLevel(self):
        self.score += self.SCORE_EXIT
        self.gameOver = True
        
    def resetLevel(self):
        self.startLevel(self.level)
    
    def addEventHandler(self, eventHandler):
        self.eventHandlers.append(eventHandler)
    
    def removeEventHandler(self, eventHandler):
        self.eventHandlers.remove(eventHandler)
    
    def processDataStreams(self):
        if self.remoteController is not None:
            for e in self.remoteController.generateEvents():
                pygame.event.post(e)

        for event in pygame.event.get():
            #print event
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == K_ESCAPE):
                self.running = False
                break
            for eh in self.eventHandlers:
                eh.handleEvent(event)

    def mainLoop(self):
        while self.running:
            if self.gameOver:
                self.resetLevel()
            self.processDataStreams()
            self.update()
            self.draw()
            self.timer.tick(self.FRAME_RATE)
        log(f"the game is over, score={self.score}")

    def mainLoopRemoteControlledTest(self):
        frame = 0
        actionGen = RemoteActionEventGenerator()
        while self.running:
            if frame <= 10:
                action = RemoteAction.RIGHT
            elif frame <= 20:
                action = RemoteAction.RIGHT_UP
            else:
                action = RemoteAction.RIGHT
            events = actionGen.actionToEvents(action)
            for e in events:
                pygame.event.post(e)
            self.processDataStreams()
            self.update()
            self.draw()
            self.timer.tick(self.FRAME_RATE)
            frame += 1
        log(f"the game is over, score={self.score}")
